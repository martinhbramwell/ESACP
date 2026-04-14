#!/usr/bin/env python3
"""
provision_kvm.py — ESACP KVM Provisioning Orchestrator (Stage 2.1)

Full lifecycle for KVM VMs:
  autoinstall wait (if needed) → start → SSH poll →
  "Fresh Install" snapshot → Ansible → "Stage 2.1 Baseline" snapshot

The provisioner detects whether a VM is mid-autoinstall and waits automatically:
  - VM shut off        → start immediately (autoinstall already done)
  - VM running + SSH up → already booted, proceed
  - VM running + no SSH → autoinstall in progress; wait for poweroff (~10–20 min),
                          then start the installed OS

Usage:
    python3 orchestration/provision_kvm.py                     # provision both VMs
    python3 orchestration/provision_kvm.py --target <hub_key>  # single VM
    python3 orchestration/provision_kvm.py --target target1
    python3 orchestration/provision_kvm.py --check             # dry run (Ansible check mode)
    python3 orchestration/provision_kvm.py --tags wireguard    # run specific Ansible tags
    python3 orchestration/provision_kvm.py --skip-fresh-snapshot  # skip "Fresh Install" snapshot
    python3 orchestration/provision_kvm.py --skip-ssh-wait     # skip post-start SSH poll
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

PROJECT_ROOT     = Path(__file__).parent.parent
ANSIBLE_DIR      = PROJECT_ROOT / "ansible"
SNAPSHOT_SCRIPT  = PROJECT_ROOT / "platforms" / "kvm" / "snapshot.py"

INVENTORY     = "kvm.yml"
PLAYBOOK      = "site-kvm.yml"
SNAPSHOT_FRESH    = "Fresh Install"
SNAPSHOT_BASELINE = "Stage 2.1 Baseline"

from tools.host_identity import HUB_KEY, HUB_WG_IP

KVM_VMS = {
    HUB_KEY: {
        "description": "Ubuntu Server 24.04 — WireGuard hub + observability stack",
        "wg_ip":       HUB_WG_IP,
    },
    "target1": {
        "description": "Ubuntu Server 24.04 — monitored host",
        "wg_ip":       "10.10.0.3",
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def banner(msg: str) -> None:
    console.print(Panel(f"[bold]{msg}[/bold]", expand=False))


def run(cmd: list[str], check: bool = True, env: dict = None, cwd: str = None) -> subprocess.CompletedProcess:
    console.print(f"[dim]→ {' '.join(cmd)}[/dim]")
    try:
        return subprocess.run(cmd, check=check, text=True, env=env, cwd=cwd)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Command failed (exit {e.returncode})[/red]")
        sys.exit(1)


def snapshot(action: str, vm: str, name: str = None) -> None:
    cmd = ["python3", str(SNAPSHOT_SCRIPT), action, vm]
    if name:
        cmd.append(name)
    run(cmd)


# ── Prerequisites ─────────────────────────────────────────────────────────────

def check_prerequisites() -> None:
    banner("Checking Prerequisites")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Tool", style="cyan", min_width=20)
    table.add_column("Status", min_width=12)
    missing = []
    for tool in ("ansible", "ansible-playbook", "virsh", "sops", "age"):
        found = subprocess.run(["which", tool], capture_output=True).returncode == 0
        table.add_row(tool, "[green]✓ Found[/green]" if found else "[red]✗ Missing[/red]")
        if not found:
            missing.append(tool)
    console.print(table)
    if missing:
        console.print(f"[red]❌ Missing: {', '.join(missing)}[/red]")
        sys.exit(1)
    console.print("[green]✅ All prerequisites satisfied[/green]")


# ── Shared Ansible environment ────────────────────────────────────────────────

def ansible_env() -> dict:
    """Return an env dict with ANSIBLE_CONFIG and SSH key set."""
    env = os.environ.copy()
    env["ANSIBLE_CONFIG"] = str(ANSIBLE_DIR / "ansible.cfg")
    env["ANSIBLE_PRIVATE_KEY_FILE"] = os.path.expanduser(
        os.environ.get("SSH_KEY_PATH", "~/.ssh/hasan_mighty")
    )
    return env


# ── VM state helpers ──────────────────────────────────────────────────────────

def vm_state(vm: str) -> str:
    """Return the current virsh domain state string (e.g. 'running', 'shut off')."""
    result = subprocess.run(["virsh", "domstate", vm], capture_output=True, text=True)
    return result.stdout.strip()


def _ansible_ping(vm: str) -> bool:
    """Run a single ansible ping against vm. Returns True on SUCCESS."""
    cmd = ["ansible", "all", "-i", f"inventory/{INVENTORY}", "-m", "ping",
           "--one-line", "--limit", vm]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            env=ansible_env(), cwd=str(ANSIBLE_DIR))
    return result.returncode == 0 and "SUCCESS" in result.stdout


def wait_for_poweroff(vm: str, timeout: int = 1800) -> bool:
    """Poll virsh domstate until the VM powers off (autoinstall complete).

    Ubuntu 24.04 autoinstall powers the VM off when finished. Typical duration
    is 10–20 minutes depending on host speed.
    """
    banner(f"Waiting for {vm} autoinstall to complete")
    console.print("  [dim]VM will power off automatically when installation finishes (~10–20 min)[/dim]")
    start = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Autoinstall running... ({task.fields[elapsed]}s)[/cyan]"),
        transient=True,
    ) as progress:
        task = progress.add_task("waiting", elapsed=0)
        while time.time() - start < timeout:
            if vm_state(vm) == "shut off":
                elapsed = int(time.time() - start)
                console.print(f"[green]✅  Autoinstall complete ({elapsed}s)[/green]")
                return True
            progress.update(task, elapsed=int(time.time() - start))
            time.sleep(10)

    console.print(f"[red]❌ Autoinstall did not complete within {timeout}s[/red]")
    return False


def ensure_vm_started(vm: str) -> None:
    """Start the VM, handling the post-autoinstall case automatically.

    Three cases:
    - shut off  → start directly (autoinstall done, or VM was stopped normally)
    - running + SSH reachable within 30s → already fully booted, nothing to do
    - running + SSH not reachable → autoinstall in progress; wait for poweroff,
                                    then start so it boots into the installed OS
    """
    state = vm_state(vm)

    if state == "shut off":
        console.print(f"  [cyan]{vm} is shut off — starting[/cyan]")
        snapshot("start", vm)
        return

    if state != "running":
        console.print(f"[red]❌ Unexpected VM state '{state}' for {vm}[/red]")
        sys.exit(1)

    # VM is running — probe SSH briefly to distinguish normal boot from autoinstall.
    console.print(f"  [cyan]{vm} is running — probing SSH for 30s[/cyan]")
    probe_start = time.time()
    while time.time() - probe_start < 30:
        if _ansible_ping(vm):
            console.print(f"  [green]✅  {vm} SSH reachable — already up[/green]")
            return
        time.sleep(5)

    # SSH not available in 30s → assume autoinstall is running.
    console.print(f"  [yellow]SSH not reachable — autoinstall appears to be running[/yellow]")
    if not wait_for_poweroff(vm):
        sys.exit(1)
    snapshot("start", vm)


# ── SSH wait ──────────────────────────────────────────────────────────────────

def wait_for_ssh(limit: str = None, timeout: int = 120) -> bool:
    banner("Waiting for SSH")
    env = ansible_env()
    start = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Polling SSH... ({task.fields[elapsed]}s / {task.fields[timeout]}s)[/cyan]"),
        transient=True,
    ) as progress:
        task = progress.add_task("waiting", elapsed=0, timeout=timeout)
        while time.time() - start < timeout:
            if _ansible_ping(limit):
                console.print("[green]✅ SSH available[/green]")
                return True
            elapsed = int(time.time() - start)
            progress.update(task, elapsed=elapsed)
            time.sleep(5)

    console.print(f"[red]❌ SSH timeout after {timeout}s[/red]")
    return False


# ── Ansible ───────────────────────────────────────────────────────────────────

def run_ansible(
    limit: str = None,
    check_mode: bool = False,
    tags: str = None,
    ask_become_pass: bool = False,
) -> None:
    banner("Running Ansible")
    env = ansible_env()

    # Run from ANSIBLE_DIR so Ansible resolves group_vars/ and roles/ correctly.
    cmd = [
        "ansible-playbook",
        "-i", f"inventory/{INVENTORY}",
        PLAYBOOK,
        "-v",
    ]
    if limit:
        cmd += ["--limit", limit]
    if check_mode:
        cmd.append("--check")
        console.print("[cyan]ℹ️  Check mode (dry run)[/cyan]")
    if tags:
        cmd += ["--tags", tags]
    if ask_become_pass:
        cmd.append("--ask-become-pass")

    run(cmd, env=env, cwd=str(ANSIBLE_DIR))
    console.print("[green]✅ Ansible complete[/green]")


# ── Per-VM lifecycle ──────────────────────────────────────────────────────────

def provision_vm(
    vm: str,
    check_mode: bool,
    tags: str,
    skip_ssh_wait: bool,
    skip_fresh_snapshot: bool,
) -> None:
    info = KVM_VMS[vm]
    banner(f"Provisioning {vm}  —  {info['description']}")

    # 0. Ensure VM is started, waiting out autoinstall if necessary.
    ensure_vm_started(vm)

    # 1. SSH poll
    if not skip_ssh_wait:
        if not wait_for_ssh(limit=vm):
            console.print(f"[red]❌ Cannot reach {vm} via SSH[/red]")
            sys.exit(1)

    # 2. "Fresh Install" snapshot
    if not skip_fresh_snapshot:
        banner(f"Snapshot: '{SNAPSHOT_FRESH}'")
        snapshot("create", vm, SNAPSHOT_FRESH)

    # 3. Ansible
    run_ansible(limit=vm, check_mode=check_mode, tags=tags)

    # 4. "Stage 2.1 Baseline" snapshot (skip in check mode — nothing was changed)
    if not check_mode:
        banner(f"Snapshot: '{SNAPSHOT_BASELINE}'")
        snapshot("create", vm, SNAPSHOT_BASELINE)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ESACP KVM Provisioner — Stage 2.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--target",
        choices=list(KVM_VMS.keys()),
        default=None,
        help="Provision a single VM (default: both)",
    )
    parser.add_argument("--check",   action="store_true", help="Ansible check mode (dry run)")
    parser.add_argument("--tags",    help="Run specific Ansible tags only")
    parser.add_argument("--skip-ssh-wait",       action="store_true",
                        help="Skip post-start SSH poll (VM already up and reachable)")
    parser.add_argument("--skip-fresh-snapshot", action="store_true",
                        help="Skip the 'Fresh Install' snapshot (VM was already snapshotted)")

    args = parser.parse_args()

    banner("ESACP KVM Provisioner — Stage 2.1")
    check_prerequisites()

    targets = [args.target] if args.target else list(KVM_VMS.keys())

    for vm in targets:
        provision_vm(
            vm=vm,
            check_mode=args.check,
            tags=args.tags,
            skip_ssh_wait=args.skip_ssh_wait,
            skip_fresh_snapshot=args.skip_fresh_snapshot,
        )

    # Configure WireGuard spoke on the controller (this host).
    # Play 4 in site-kvm.yml targets 'localhost' (connection: local).
    # It is always skipped when --limit <vm> is used above, so we run it
    # explicitly here.  Skip in single-target mode — user may be doing
    # incremental work and doesn't want to reconfigure the host mid-flight.
    if not args.target and not args.check:
        banner("Configuring controller WireGuard spoke")
        console.print("[cyan]ℹ️  Your sudo password is required to configure WireGuard on this host.[/cyan]")
        run_ansible(limit="localhost", tags=args.tags, ask_become_pass=True)

    banner("✅ All provisioning complete!")

    table = Table(title="KVM Services (via WireGuard)", header_style="bold cyan")
    table.add_column("Host", style="cyan")
    table.add_column("Service")
    table.add_column("Address")
    table.add_row(HUB_KEY, "Grafana",     f"http://{HUB_WG_IP}:3000")
    table.add_row(HUB_KEY, "Prometheus",  f"http://{HUB_WG_IP}:9090")
    table.add_row(HUB_KEY, "Alertmanager",f"http://{HUB_WG_IP}:9093")
    table.add_row("target1",   "node_exporter metrics", "http://10.10.0.3:9100/metrics")
    console.print(table)

    return 0


if __name__ == "__main__":
    sys.exit(main())
