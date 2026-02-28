#!/usr/bin/env python3
"""
ESACP Failure Injection Runner
Executes a named chaos scenario against a classified lab/staging VM.

Usage:
    python3 orchestration/chaos/run_scenario.py --scenario <name> [--vm <vmname>] [--snapshot-name <name>]

Required environment variables:
    VM_IP          IP address of the target VM
    VM_HOSTNAME    VirtualBox VM name (overridden by --vm)
    SSH_KEY_PATH   Path to SSH private key (default: ~/.ssh/id_ed25519)
    SNAPSHOT_NAME  Snapshot name to revert to (overridden by --snapshot-name)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Confirm
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------------
# VBoxManage discovery (mirrored from revertToBaseline.py)
# ---------------------------------------------------------------------------

_VBOXMANAGE_WSL_PATH = "/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"


def find_vboxmanage():
    """Locate VBoxManage, handling native Linux and WSL on Windows."""
    for candidate in ("VBoxManage", "VBoxManage.exe"):
        if shutil.which(candidate):
            return candidate
    if Path(_VBOXMANAGE_WSL_PATH).exists():
        return _VBOXMANAGE_WSL_PATH
    return None


_VBOXMANAGE = find_vboxmanage()


# ---------------------------------------------------------------------------
# Inventory classification (fail-closed, §6.3)
# ---------------------------------------------------------------------------

def _collect_host_groups(node: dict, host: str, path: list[str]) -> list[str]:
    """Recursively walk an inventory 'children' tree and collect group names containing host."""
    found_groups = []
    hosts = node.get("hosts") or {}
    if host in hosts:
        found_groups.extend(path)
    children = node.get("children") or {}
    for group_name, child in children.items():
        if child is None:
            child = {}
        found_groups.extend(_collect_host_groups(child, host, path + [group_name]))
    return found_groups


def check_target_classification(inventory_path: str, target_host: str) -> None:
    """
    Parse inventory YAML and enforce fail-closed host classification.

    Exits with code 1 if:
      - host is in 'production' or 'protected' group
      - host is not classified in any recognised group
    Proceeds silently if host is in 'lab' or 'staging'.
    """
    try:
        with open(inventory_path) as f:
            inventory = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]❌ Inventory file not found: {inventory_path}[/red]")
        sys.exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]❌ Failed to parse inventory YAML: {e}[/red]")
        sys.exit(1)

    all_node = inventory.get("all", {})
    groups = _collect_host_groups(all_node, target_host, [])

    if not groups:
        console.print(
            f"[red]❌ Host '{target_host}' is not present in inventory '{inventory_path}'.\n"
            "Refusing to run against an unclassified target.[/red]"
        )
        sys.exit(1)

    blocked = [g for g in groups if g in ("production", "protected")]
    if blocked:
        console.print(
            f"[red]❌ Host '{target_host}' is in group(s) {blocked}.\n"
            "Chaos scenarios must not run against production/protected targets.[/red]"
        )
        sys.exit(1)

    allowed = [g for g in groups if g in ("lab", "staging")]
    if not allowed:
        console.print(
            f"[red]❌ Host '{target_host}' is in group(s) {groups} but none are 'lab' or 'staging'.\n"
            "Refusing to run against an unclassified target.[/red]"
        )
        sys.exit(1)

    console.print(
        f"[green]✅ Target '{target_host}' classified as {allowed} — approved for injection.[/green]"
    )


# ---------------------------------------------------------------------------
# SSH helpers
# ---------------------------------------------------------------------------

def ssh_run(host: str, user: str, key: str, cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a command on the remote host via SSH."""
    return subprocess.run(
        [
            "ssh",
            "-i", key,
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            f"{user}@{host}",
            cmd,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def scp_file(local_path: str, host: str, user: str, key: str, remote_path: str) -> None:
    """Copy a file to the remote host via SCP."""
    subprocess.run(
        [
            "scp",
            "-i", key,
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no",
            local_path,
            f"{user}@{host}:{remote_path}",
        ],
        check=True,
    )


# ---------------------------------------------------------------------------
# VBoxManage helpers
# ---------------------------------------------------------------------------

def run_vboxmanage(args: list[str], check: bool = True) -> subprocess.CompletedProcess | None:
    if _VBOXMANAGE is None:
        console.print("[red]❌ VBoxManage not found. Cannot manage snapshots.[/red]")
        sys.exit(1)
    cmd = [_VBOXMANAGE] + args
    console.print(f"[dim]→ {' '.join(cmd)}[/dim]")
    try:
        return subprocess.run(cmd, check=check, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ VBoxManage failed: {e.stderr.strip()}[/red]")
        if check:
            sys.exit(1)
        return None


def list_snapshots(vm: str) -> str:
    result = run_vboxmanage(["snapshot", vm, "list"], check=False)
    return result.stdout if result else "(none)"


def take_snapshot(vm: str, scenario_name: str) -> None:
    run_vboxmanage(["snapshot", vm, "take", f"Before {scenario_name} test"])


# ---------------------------------------------------------------------------
# Failure injection methods
# ---------------------------------------------------------------------------

MEMORY_PRESSURE_SCRIPT = """\
#!/usr/bin/env python3
import os, sys, time

with open('/proc/meminfo') as f:
    info = {k.strip(): v.strip() for line in f for k, v in [line.split(':', 1)]}

mem_available_kb = int(info['MemAvailable'].split()[0])
ceiling_percent = int(sys.argv[1]) if len(sys.argv) > 1 else 40
allocate_kb = int(mem_available_kb * ceiling_percent / 100)
allocate_bytes = allocate_kb * 1024

print(f'Allocating {allocate_bytes // (1024*1024)} MB ({ceiling_percent}% of MemAvailable)...')
buf = bytearray(allocate_bytes)
print('Allocation complete. Holding for 240 seconds...')
time.sleep(240)
print('Done.')
"""


def inject(scenario_name: str, params: dict, host: str, user: str, key: str) -> None:
    """Dispatch to the correct injection method for the scenario."""

    def _ssh(cmd: str, timeout: int = 30) -> None:
        try:
            result = ssh_run(host, user, key, cmd, timeout=timeout)
            if result.returncode != 0:
                console.print(f"[yellow]⚠️  SSH command exited {result.returncode}: {result.stderr.strip()}[/yellow]")
        except subprocess.TimeoutExpired:
            console.print("[yellow]⚠️  SSH unreachable — monitoring only. Revert available.[/yellow]")
        except ConnectionRefusedError:
            console.print("[yellow]⚠️  SSH connection refused — monitoring only. Revert available.[/yellow]")

    if scenario_name == "disk_pressure":
        # Fill ~90% of available space in /tmp using a 4 GB file (adjust if needed)
        _ssh("dd if=/dev/zero of=/tmp/esacp_fill bs=1M count=4096 2>/dev/null &")

    elif scenario_name == "cpu_saturation":
        workers = params.get("cpu_workers", 4)
        duration = params.get("timeout_seconds", 120)
        _ssh(
            f'nohup timeout {duration} bash -c '
            f'"for i in $(seq 1 {workers}); do yes > /dev/null & done; wait" '
            f'>/dev/null 2>&1 &'
        )

    elif scenario_name == "memory_pressure":
        ceiling = params.get("memory_ceiling_percent", 40)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(MEMORY_PRESSURE_SCRIPT)
            local_script = f.name
        try:
            scp_file(local_script, host, user, key, "/tmp/esacp_mem_pressure.py")
        finally:
            os.unlink(local_script)
        _ssh(f"nohup python3 /tmp/esacp_mem_pressure.py {ceiling} >/tmp/esacp_mem.log 2>&1 &")

    elif scenario_name == "log_storm":
        _ssh(
            'docker run -d --rm --name esacp-log-storm ubuntu '
            'bash -c "while true; do echo LOG_STORM; done"'
        )

    elif scenario_name == "container_restart_loop":
        _ssh(
            "docker run -d --restart=always --name esacp-restart-test "
            "alpine sh -c 'exit 1'"
        )

    elif scenario_name == "prometheus_stopped":
        _ssh("docker stop prometheus")

    elif scenario_name == "alertmanager_stopped":
        _ssh("docker stop alertmanager")

    elif scenario_name == "loki_stopped":
        _ssh("docker stop loki")

    elif scenario_name == "promtail_stopped":
        _ssh("docker stop promtail")

    elif scenario_name == "grafana_stopped":
        _ssh("docker stop grafana")

    else:
        console.print(f"[red]❌ Unknown scenario '{scenario_name}'[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main 9-step lifecycle
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    # ── Load scenarios.yml ────────────────────────────────────────────────
    scenarios_path = Path(__file__).parent / "scenarios.yml"
    try:
        with open(scenarios_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]❌ scenarios.yml not found at {scenarios_path}[/red]")
        return 1

    scenario_name = args.scenario
    scenarios = config.get("scenarios", {})
    if scenario_name not in scenarios:
        console.print(
            f"[red]❌ Unknown scenario '{scenario_name}'. "
            f"Available: {', '.join(scenarios.keys())}[/red]"
        )
        return 1

    params = scenarios[scenario_name]

    # ── Resolve connection parameters ─────────────────────────────────────
    vm = args.vm or os.environ.get("VM_HOSTNAME", "")
    snapshot_name = args.snapshot_name or os.environ.get("SNAPSHOT_NAME", "")
    host = os.environ.get("VM_IP", "")
    user = os.environ.get("VM_USER", "ernest")
    key = os.environ.get("SSH_KEY_PATH", str(Path.home() / ".ssh" / "id_ed25519"))

    if not host:
        console.print("[red]❌ VM_IP environment variable is not set.[/red]")
        return 1
    if not vm:
        console.print("[red]❌ VM_HOSTNAME env var or --vm argument is required.[/red]")
        return 1

    # ── Inventory classification check (fail-closed) ──────────────────────
    inventory_path = config.get("ansible", {}).get("inventory_file", "ansible/inventory/dev.yml")
    check_target_classification(inventory_path, "console")

    console.print(Panel(
        f"[bold]ESACP Failure Injection Runner[/bold]\n"
        f"Scenario: [cyan]{scenario_name}[/cyan]  •  VM: [cyan]{vm}[/cyan]  •  Host: [cyan]{host}[/cyan]",
        expand=False,
    ))

    # ── Step 1: Advise snapshot will be created ───────────────────────────
    console.print("\n[bold]Step 1 — Snapshot advisory[/bold]")
    console.print(
        f"A VirtualBox snapshot will be taken before injection so you can revert cleanly.\n"
        f"Snapshot will be named: [cyan]Before {scenario_name} test[/cyan]"
    )

    # ── Step 2: List existing snapshots ──────────────────────────────────
    console.print("\n[bold]Step 2 — Existing snapshots[/bold]")
    snapshot_output = list_snapshots(vm)
    table = Table(title=f"Snapshots for VM '{vm}'", show_lines=True)
    table.add_column("Snapshot listing", style="dim")
    for line in snapshot_output.splitlines():
        table.add_row(line)
    console.print(table)
    console.print("[dim]Consider pruning old snapshots to conserve disk space.[/dim]")

    # ── Step 3: Confirm ───────────────────────────────────────────────────
    console.print("\n[bold]Step 3 — Confirm[/bold]")
    if not Confirm.ask("Create snapshot and proceed with failure injection?"):
        console.print("[yellow]Aborted by user.[/yellow]")
        return 0

    # ── Step 4: Take snapshot ─────────────────────────────────────────────
    console.print("\n[bold]Step 4 — Taking snapshot[/bold]")
    take_snapshot(vm, scenario_name)
    console.print(f"[green]✅ Snapshot 'Before {scenario_name} test' created.[/green]")

    # ── Step 5: Print scenario briefing ──────────────────────────────────
    console.print("\n[bold]Step 5 — Scenario briefing[/bold]")
    briefing = f"""
## Expected guest behaviour

{params.get('expected_guest_behavior', '').strip()}

## Expected Grafana manifestations

{params.get('expected_grafana_manifestations', '').strip()}

**Injection timeout:** {params.get('timeout_seconds', 120)} s
**Estimated consequence delay:** {params.get('estimated_consequence_delay_seconds', 30)} s
"""
    console.print(Markdown(briefing))

    # ── Step 6: Inject failure ────────────────────────────────────────────
    console.print("\n[bold]Step 6 — Injecting failure[/bold]")
    console.print(f"[yellow]⚡ Injecting scenario '{scenario_name}' on {user}@{host}...[/yellow]")
    try:
        inject(scenario_name, params, host, user, key)
        console.print("[green]✅ Injection command dispatched.[/green]")
    except Exception as e:
        console.print(f"[red]❌ Injection error: {e}[/red]")
        console.print("[yellow]Continuing to monitoring phase — revert remains available.[/yellow]")

    # ── Step 7 & 8: Countdown timer ───────────────────────────────────────
    consequence_delay = params.get("estimated_consequence_delay_seconds", 30)
    timer_duration = max(120, 4 * consequence_delay)

    console.print(f"\n[bold]Step 7 — Monitoring window ({timer_duration}s)[/bold]")
    console.print(
        "Watch Grafana now. The timer below counts down your observation window.\n"
        "Press Ctrl+C at any time to skip to the revert prompt."
    )

    timed_out = True
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Observation window ({scenario_name})", total=timer_duration
            )
            for elapsed in range(timer_duration):
                time.sleep(1)
                progress.update(task, advance=1)
        timed_out = True
    except KeyboardInterrupt:
        console.print("\n[yellow]Timer interrupted by user.[/yellow]")
        timed_out = False

    # ── Step 8: Handle timer expiry ───────────────────────────────────────
    console.print("\n[bold]Step 8 — Timer outcome[/bold]")
    if timed_out:
        console.print("[yellow]⏱️  Observation window expired.[/yellow]")
        choice = ""
        while choice not in ("c", "r"):
            choice = console.input(
                "Continue waiting [c] or revert now [r]? "
            ).strip().lower()
            if choice == "c":
                extra = console.input("How many additional seconds? ").strip()
                try:
                    extra_secs = int(extra)
                except ValueError:
                    extra_secs = 60
                console.print(f"[dim]Waiting {extra_secs}s more...[/dim]")
                time.sleep(extra_secs)
                break
    else:
        console.print("[green]User signalled ready to proceed.[/green]")

    # ── Step 9: Revert ────────────────────────────────────────────────────
    console.print("\n[bold]Step 9 — Revert to snapshot[/bold]")
    if Confirm.ask("Revert VM to snapshot now?"):
        revert_script = Path(__file__).parent.parent / "revertToBaseline.py"
        snap = snapshot_name or f"Before {scenario_name} test"
        console.print(f"[cyan]Calling revertToBaseline.py --vm {vm} --snapshot '{snap}'...[/cyan]")
        subprocess.run(
            [sys.executable, str(revert_script), "--vm", vm, "--snapshot", snap],
            check=False,
        )
    else:
        console.print(
            "[yellow]⚠️  Revert skipped. Remember to manually revert or clean up the VM.[/yellow]"
        )

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ESACP Failure Injection Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--scenario", required=True,
        help="Name of the scenario to run (must exist in scenarios.yml)",
    )
    parser.add_argument(
        "--vm", default=None,
        help="VirtualBox VM name (default: $VM_HOSTNAME)",
    )
    parser.add_argument(
        "--snapshot-name", default=None,
        help="Snapshot name to revert to (default: $SNAPSHOT_NAME)",
    )
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
