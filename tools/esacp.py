#!/usr/bin/env python3
"""
esacp — ESACP unified lab management CLI

12 subcommands for building, provisioning, and validating the ESACP KVM lab.
All defaults are derived from project config files (hosts_map.yml, group_vars/).

Usage:
    python tools/esacp.py <subcommand> [options]

Subcommands:
    confirmPrerequisites           Check and install required host software
    validateKeys                   Verify SOPS/age key decryption and WireGuard key structure
    clearKnownHosts                Remove stale SSH known_hosts entries for ESACP VMs
    destroyVM <vm>                 Destroy a KVM VM and all its storage
    buildVM <vm>                   Build seed ISO, create VM, wait for autoinstall
    provisionVM <vm>               Run Ansible provisioning (task names and errors only)
    provision <vm>                 Full pipeline: create VM + provision + differentiate (stages 1–9)
    destroy <vm>                   Full teardown: VM + WireGuard + hosts_map + SOPS keys
    verifyVPN                      Test WireGuard connectivity and inter-VM routing
    validateObservability          Run the 27-check observability validation suite
    snapShotVM <vm> [name]         Create or list snapshots for a VM
    displayConfiguration           Show the lab configuration tree
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is importable (needed for `from tools.pipeline...` imports)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import yaml
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree
except ImportError as exc:
    print(f"Missing dependency: {exc}\nInstall with: pip3 install rich pyyaml")
    sys.exit(1)


console = Console()

PROJECT_ROOT  = Path(__file__).parent.parent
ANSIBLE_DIR   = PROJECT_ROOT / "ansible"
PLATFORMS_KVM = PROJECT_ROOT / "platforms" / "kvm"
IMAGES_DIR    = Path("/var/lib/libvirt/images")
SNAPSHOT_PY   = PLATFORMS_KVM / "snapshot.py"


# ── Config loading ─────────────────────────────────────────────────────────────

def load_hosts_map() -> dict:
    with open(PROJECT_ROOT / "hosts_map.yml") as f:
        return yaml.safe_load(f)


def load_group_vars(name: str) -> dict:
    path = ANSIBLE_DIR / "group_vars" / f"{name}.yml"
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def load_config() -> dict:
    return {
        "hosts": load_hosts_map(),
        "all":   load_group_vars("all"),
        "kvm":   load_group_vars("kvm"),
    }


def kvm_hosts(config: dict) -> dict:
    return config["hosts"].get("groups", {}).get("kvm", {})


def all_vm_names(config: dict) -> list:
    return list(kvm_hosts(config).keys())


def controller_info(config: dict) -> dict:
    return config["hosts"].get("groups", {}).get("controller", {}).get("local", {})


def hub_vm(config: dict) -> Optional[str]:
    for name, info in kvm_hosts(config).items():
        if info.get("wg_role") == "hub":
            return name
    return None


def ssh_key_path(config: dict) -> str:
    raw = config["kvm"].get("ansible_ssh_private_key_file", "~/.ssh/hasan_mighty")
    raw = raw.replace("{{ lookup('env', 'HOME') }}", os.environ.get("HOME", "~"))
    return os.path.expanduser(raw)


def vm_user(config: dict) -> str:
    return config["kvm"].get("ansible_user", "you")


def ansible_env(config: dict) -> dict:
    env = os.environ.copy()
    env["ANSIBLE_CONFIG"] = str(ANSIBLE_DIR / "ansible.cfg")
    env["ANSIBLE_PRIVATE_KEY_FILE"] = ssh_key_path(config)
    return env


# ── Shared helpers ─────────────────────────────────────────────────────────────

def banner(msg: str) -> None:
    console.print(Panel(f"[bold]{msg}[/bold]", expand=False))


def confirm(msg: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    console.print(f"[bold yellow]{msg}[/bold yellow] [{hint}]: ", end="")
    resp = sys.stdin.readline().strip().lower()
    if resp == "":
        return default
    return resp in ("y", "yes")


def vm_state(vm: str) -> str:
    result = subprocess.run(["virsh", "domstate", vm], capture_output=True, text=True)
    return result.stdout.strip()


def ansible_ping(vm: str, config: dict) -> bool:
    result = subprocess.run(
        ["ansible", "all", "-i", "inventory/kvm.yml", "-m", "ping",
         "--one-line", "--limit", vm],
        capture_output=True, text=True,
        env=ansible_env(config), cwd=str(ANSIBLE_DIR),
    )
    return result.returncode == 0 and "SUCCESS" in result.stdout


def ssh_run(host_ip: str, user: str, key: str, cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-i", key,
         "-o", "StrictHostKeyChecking=accept-new",
         "-o", "ConnectTimeout=10",
         f"{user}@{host_ip}", cmd],
        capture_output=True, text=True,
    )


# ── 1. confirmPrerequisites ────────────────────────────────────────────────────

def cmd_confirm_prerequisites(args, config: dict) -> int:
    from tools.pipeline.stages.preflight.check_tools import (
        check_tools, MANUAL_INSTALL_HINTS,
    )
    from tools.pipeline.stages.preflight.check_files import check_files

    banner("Confirm Prerequisites")
    console.print("[bold cyan]Tool checks[/bold cyan]")
    tool_status = check_tools(emit=console.print)

    console.print()
    console.print("[bold cyan]File checks[/bold cyan]")
    file_results = check_files(str(PROJECT_ROOT), ssh_key_path(config), emit=console.print)
    file_issues = [(p, d) for p, d, exists in file_results if not exists]

    console.print()
    if not tool_status.missing_apt and not tool_status.missing_manual and not file_issues:
        console.print("[green]✅  All prerequisites satisfied.[/green]")
        return 0

    if tool_status.missing_apt:
        pkgs = " ".join(sorted(tool_status.missing_apt))
        console.print(f"[yellow]Missing apt packages:[/yellow] {pkgs}")
        if confirm("Install now via apt?"):
            result = subprocess.run(["sudo", "apt", "install", "-y"] + sorted(tool_status.missing_apt))
            if result.returncode != 0:
                console.print("[red]❌  apt install failed.[/red]")
                return 1
            console.print("[green]✅  Packages installed.[/green]")
        else:
            console.print(f"[dim]Re-run after: sudo apt install -y {pkgs}[/dim]")

    if tool_status.missing_manual:
        console.print()
        console.print("[yellow]Manual installs required:[/yellow]")
        reported = set()
        for tool, pkg in tool_status.missing_manual:
            if pkg not in reported:
                hint = MANUAL_INSTALL_HINTS.get(tool, MANUAL_INSTALL_HINTS.get(pkg, ""))
                console.print(f"  [cyan]{pkg}[/cyan]: {hint}")
                reported.add(pkg)

    if file_issues:
        console.print()
        console.print("[yellow]Missing files:[/yellow]")
        ssh_key = Path(ssh_key_path(config))
        for path, desc in file_issues:
            if "age/keys.txt" in str(path):
                console.print(f"  age key: age-keygen -o {path}")
                console.print(f"           then add the public key as a recipient in .sops.yaml")
            elif ".pub" in str(path):
                console.print(f"  SSH public key: ssh-keygen -y -f {ssh_key} > {path}")
            elif "hasan_mighty" in str(path):
                console.print(f"  SSH key: generate with ssh-keygen -t ed25519 -f {path}")
            else:
                console.print(f"  {desc}: {path} — see SETUP_GUIDE.md")

    return 1 if (tool_status.missing_manual or file_issues) else 0


# ── 2. validateKeys ────────────────────────────────────────────────────────────

def cmd_validate_keys(args, config: dict) -> int:
    from tools.pipeline.stages.preflight.check_keys import check_keys

    banner("Validate Keys")
    expected = list(kvm_hosts(config).keys()) + ["controller"]
    result = check_keys(
        project_root=str(PROJECT_ROOT),
        expected_hosts=expected,
        hub_name=hub_vm(config),
        emit=console.print,
    )
    console.print()
    if result.success:
        console.print("[green]✅  All WireGuard keys present and decryptable.[/green]")
        return 0
    console.print(f"[red]❌  {result.message} — re-run config/wireguard/generate_keys.sh[/red]")
    return 1


# ── 3. clearKnownHosts ────────────────────────────────────────────────────────

def cmd_clear_known_hosts(args, config: dict) -> int:
    from tools.pipeline.stages.common.known_hosts import known_hosts_entries, remove_known_hosts

    banner("Clear Known Hosts")

    all_entries = []
    for name, info in kvm_hosts(config).items():
        for e in known_hosts_entries(info):
            if e not in all_entries:
                all_entries.append(e)

    console.print(f"Removing up to {len(all_entries)} entries from ~/.ssh/known_hosts:")
    for entry in all_entries:
        console.print(f"  [dim]{entry}[/dim]")
    console.print()

    noop_emit = lambda msg: None
    removed = remove_known_hosts(all_entries, noop_emit)
    console.print(f"[green]✅  Done ({removed} removed, rest were not present).[/green]")
    return 0


# ── 4. destroyVM ──────────────────────────────────────────────────────────────

def cmd_destroy_vm(args, config: dict) -> int:
    vm = args.vm
    banner(f"Destroy VM: {vm}")

    if subprocess.run(["virsh", "dominfo", vm], capture_output=True).returncode != 0:
        console.print(f"[yellow]VM '{vm}' does not exist — nothing to do.[/yellow]")
        return 0

    state = vm_state(vm)
    console.print(f"  State     : [cyan]{state}[/cyan]")

    snap_result = subprocess.run(
        ["virsh", "snapshot-list", vm, "--name"], capture_output=True, text=True
    )
    snapshots = [s for s in snap_result.stdout.strip().splitlines() if s]
    if snapshots:
        console.print(f"  Snapshots : [yellow]{len(snapshots)}[/yellow]")
        for s in snapshots:
            console.print(f"    [dim]• {s}[/dim]")

    disk = IMAGES_DIR / f"{vm}.qcow2"
    seed = IMAGES_DIR / f"{vm}-seed.iso"
    for f in (disk, seed):
        if f.exists():
            size = f.stat().st_size // (1024 * 1024)
            console.print(f"  Disk      : [dim]{f}[/dim] ({size} MiB)")

    console.print()
    console.print("[bold red]This permanently destroys the VM, all snapshots, and all storage.[/bold red]")
    if not confirm(f"Destroy {vm}?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return 0

    if state == "running":
        console.print(f"  Forcing off {vm}...")
        subprocess.run(["virsh", "destroy", vm], capture_output=True)

    console.print(f"  Undefining {vm} (--snapshots-metadata --remove-all-storage)...")
    result = subprocess.run(
        ["virsh", "undefine", vm, "--snapshots-metadata", "--remove-all-storage"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]❌  virsh undefine failed: {result.stderr.strip()}[/red]")
        return 1

    if seed.exists():
        console.print(f"  Removing seed ISO: {seed}")
        subprocess.run(["sudo", "rm", "-f", str(seed)])

    console.print(f"[green]✅  {vm} destroyed.[/green]")
    return 0


# ── 5. buildVM ────────────────────────────────────────────────────────────────

def cmd_build_vm(args, config: dict) -> int:
    """Build a VM from scratch via autoinstall — delegates to pipeline primitive."""
    from tools.pipeline.orchestration.build_vm import build_vm

    vm = args.vm
    vm_info = kvm_hosts(config).get(vm, {})
    banner(f"Build VM: {vm}")

    messages: list[str] = []
    try:
        build_vm(vm, vm_info, str(PROJECT_ROOT), ssh_key_path(config),
                 lambda msg: (messages.append(msg), console.print(msg)))
    except RuntimeError as exc:
        console.print(f"[red]❌  {exc}[/red]")
        return 1

    console.print()
    console.print(f"[green]✅  {vm} is built and SSH-ready.[/green]")
    console.print(f"    Next: [cyan]./tools/esacp.py provisionVM {vm}[/cyan]")
    return 0


# ── 6. provisionVM ────────────────────────────────────────────────────────────

def _virsh_snapshot_list(vm: str, hypervisor: str) -> list[str]:
    """Return snapshot names for a VM, routing to the correct hypervisor."""
    if hypervisor:
        cmd = ["ssh", hypervisor,
               f"virsh --connect qemu:///system snapshot-list {vm} --name"]
    else:
        cmd = ["virsh", "snapshot-list", vm, "--name"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip().splitlines() if r.returncode == 0 else []


def _virsh_snapshot_create(vm: str, name: str, hypervisor: str) -> bool:
    """Take a snapshot, routing to the correct hypervisor. Returns True on success."""
    if hypervisor:
        cmd = ["ssh", hypervisor,
               f"virsh --connect qemu:///system snapshot-create-as {vm} '{name}' --atomic"]
    else:
        cmd = ["virsh", "snapshot-create-as", vm, name, "--atomic"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0


def cmd_provision_vm(args, config: dict) -> int:
    vm = args.vm
    banner(f"Provision VM: {vm}")

    vm_info    = kvm_hosts(config).get(vm, {})
    hypervisor = vm_info.get("hypervisor", "local")

    # Step 1 — Verify SSH
    console.print("[bold]Step 1/4:[/bold] Verify SSH reachable")
    if not ansible_ping(vm, config):
        console.print(f"[red]❌  Cannot reach {vm} via SSH.[/red]")
        console.print(f"    Start it with: [cyan]virsh start {vm}[/cyan]")
        return 1
    console.print("  [green]✓[/green] SSH reachable")

    # Step 2 — Fresh Install snapshot
    console.print()
    console.print("[bold]Step 2/4:[/bold] Fresh Install snapshot")
    existing = _virsh_snapshot_list(vm, hypervisor)

    if args.skip_fresh_snapshot or "Fresh Install" in existing:
        console.print("  [dim]Skipping (already exists or --skip-fresh-snapshot)[/dim]")
    else:
        if _virsh_snapshot_create(vm, "Fresh Install", hypervisor):
            console.print("  [green]✓[/green] 'Fresh Install' snapshot taken")
        else:
            console.print("  [yellow]⚠️  Snapshot failed — continuing[/yellow]")

    # Step 3 — Ansible
    console.print()
    console.print("[bold]Step 3/4:[/bold] Ansible provisioning [dim](task names and changes only)[/dim]")
    console.print()

    cmd = [
        "ansible-playbook",
        "-i", "inventory/kvm.yml",
        "site-kvm.yml",
        "--limit", vm,
    ]
    if args.check:
        cmd.append("--check")
        console.print("[cyan]ℹ️  Check mode — no changes will be made[/cyan]")

    from tools.pipeline.stages.common.ansible_output import filter_ansible_line
    filter_state: dict = {"current_task": "", "in_recap": False}
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=ansible_env(config),
        cwd=str(ANSIBLE_DIR),
        bufsize=1,
    )
    for raw_line in proc.stdout:
        formatted = filter_ansible_line(raw_line.rstrip(), filter_state)
        if formatted is not None:
            console.print(formatted)
    proc.wait()

    if proc.returncode != 0:
        console.print(f"[red]❌  Ansible failed (exit {proc.returncode})[/red]")
        return 1

    console.print()
    console.print("  [green]✓[/green] Ansible complete")

    # Step 4 — Baseline snapshot
    console.print()
    console.print("[bold]Step 4/4:[/bold] Baseline snapshot")
    if args.check:
        console.print("  [dim]Skipping (check mode)[/dim]")
    else:
        if _virsh_snapshot_create(vm, "Baseline", hypervisor):
            console.print("  [green]✓[/green] 'Baseline' snapshot taken")
        else:
            console.print("  [yellow]⚠️  Snapshot failed — continuing[/yellow]")

    console.print()
    console.print(f"[green]✅  {vm} provisioned.[/green]")
    return 0


# ── 6b. provision (full pipeline) ─────────────────────────────────────────────

def cmd_provision(args, config: dict) -> int:
    """Full provision pipeline: create VM + configure + differentiate (stages 1–9).

    Same pipeline as POST /api/provision/erpnext, run synchronously from CLI.
    """
    hostname = args.vm
    banner(f"Provision (full pipeline): {hostname}")

    vm_info = kvm_hosts(config).get(hostname, {})
    virbr0_ip = vm_info.get("virbr0_ip")
    if not virbr0_ip:
        console.print(f"[red]No virbr0_ip for '{hostname}' in hosts_map.yml[/red]")
        return 1

    if vm_info.get("wg_role") == "hub":
        console.print(f"[red]Cannot provision hub node '{hostname}' — use rebuild_lab.sh[/red]")
        return 1

    from tools.pipeline.macro.provision import run
    from tools.host_identity import ZONE_DOMAINS

    def emit(msg: str) -> None:
        console.print(msg)

    try:
        run(
            hostname=hostname,
            virbr0_ip=virbr0_ip,
            project_root=str(PROJECT_ROOT),
            emit=emit,
        )
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        console.print(f"[red]Pipeline failed: {exc}[/red]")
        return 1

    zone = next(
        (g for g in vm_info.get("ansible_groups", [])
         if g in ("production", "staging", "development")),
        "development",
    )
    domain = ZONE_DOMAINS.get(zone, "iridium.blue")
    console.print()
    console.print(f"[green]Provision complete — ERPNext at https://{hostname}.{domain}[/green]")
    return 0


# ── 6c. destroy (full teardown) ──────────────────────────────────────────────

def cmd_destroy(args, config: dict) -> int:
    """Full teardown: WG peer → VM → hosts_map → group_vars → inventory → SOPS."""
    hostname = args.vm
    banner(f"Destroy (full teardown): {hostname}")

    vm_info = kvm_hosts(config).get(hostname, {})
    if not vm_info:
        console.print(f"[red]'{hostname}' not found in hosts_map.yml[/red]")
        return 1

    if vm_info.get("wg_role") == "hub":
        console.print(f"[red]Cannot destroy hub node '{hostname}' — this would break the entire mesh[/red]")
        return 1

    console.print("[bold red]This permanently destroys the VM, all snapshots, WireGuard keys,[/bold red]")
    console.print("[bold red]and removes the host from all configuration files.[/bold red]")
    if not confirm(f"Destroy {hostname}?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return 0

    try:
        from tools.pipeline.macro.destroy import run
        run(hostname, vm_info, str(PROJECT_ROOT), lambda msg: console.print(msg))
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        console.print(f"[red]Destroy failed: {exc}[/red]")
        return 1

    console.print()
    console.print(f"[green]Destroy complete — {hostname} fully removed.[/green]")
    return 0


# ── 7. verifyVPN ──────────────────────────────────────────────────────────────

def cmd_verify_vpn(args, config: dict) -> int:
    from tools.pipeline.orchestration.verify_vpn import verify_vpn

    banner("Verify WireGuard VPN")
    all_ok = verify_vpn(
        hosts=kvm_hosts(config),
        vm_user=vm_user(config),
        ssh_key=ssh_key_path(config),
        emit=console.print,
    )
    console.print()
    if all_ok:
        console.print("[green]✅  All WireGuard connectivity checks passed.[/green]")
    else:
        console.print("[red]❌  Some connectivity checks failed.[/red]")
    return 0 if all_ok else 1


# ── 8. validateObservability ──────────────────────────────────────────────────

def cmd_validate_observability(args, config: dict) -> int:
    from tools.pipeline.orchestration.observability_creds import (
        source_grafana_creds,
        validate_observability,
    )

    banner("Validate Observability")

    script = PROJECT_ROOT / "orchestration" / "validate_observability.py"
    if not script.exists():
        console.print(f"[red]❌  Script not found: {script}[/red]")
        return 1

    console.print("Retrieving Grafana credentials...")
    user, password = source_grafana_creds(
        vm_user=vm_user(config),
        ssh_key=ssh_key_path(config),
        emit=console.print,
    )
    if password is None:
        password = getpass.getpass("Grafana admin password: ")

    return validate_observability(user, password, str(script), verbose=args.verbose)


# ── 9. snapShotVM ─────────────────────────────────────────────────────────────

def cmd_snapshot_vm(args, config: dict) -> int:
    vm   = args.vm
    name = args.name

    if name:
        banner(f"Snapshot: {vm} / {name}")
        result = subprocess.run(["python3", str(SNAPSHOT_PY), "create", vm, name])
    else:
        banner(f"Snapshots: {vm}")
        result = subprocess.run(["python3", str(SNAPSHOT_PY), "list", vm])

    return result.returncode


# ── 10. displayConfiguration ──────────────────────────────────────────────────

def _src(rel_path: str) -> str:
    """Return a dim 'source file' annotation for tree nodes."""
    return f"[dim]← {rel_path}[/dim]"


def cmd_display_configuration(args, config: dict) -> int:
    banner("Lab Configuration")

    hosts_map = config["hosts"]
    all_vars  = config["all"]
    kvm_vars  = config["kvm"]

    # Relative path helpers (shown alongside each value)
    F_HOSTS   = "hosts_map.yml"
    F_ALL     = "ansible/group_vars/all.yml"
    F_KVM     = "ansible/group_vars/kvm.yml"
    F_LAB     = "ansible/group_vars/lab.yml"
    F_KEYS    = "config/wireguard/keys.sops.yml"

    tree = Tree("[bold cyan]ESACP[/bold cyan]")

    # ── WireGuard Network ─────────────────────────────────────────
    wg = tree.add(f"[bold]WireGuard Network[/bold]  {_src(F_HOSTS)}")
    wg.add(f"Subnet  : [cyan]{hosts_map.get('wireguard_subnet', '—')}[/cyan]")
    wg.add(f"Port    : [cyan]{hosts_map.get('wireguard_port', '—')}[/cyan]  (UDP)")

    pubkeys = wg.add(f"Public keys  {_src(F_ALL)}")
    for varname, val in all_vars.items():
        if varname.startswith("wg_pubkey_"):
            label = varname.removeprefix("wg_pubkey_")
            pubkeys.add(f"{label:<12}: [dim]{val}[/dim]")

    encrypted = wg.add(f"Private keys / PSKs  {_src(F_KEYS)}")
    encrypted.add("[dim](SOPS/age encrypted — run validateKeys to verify)[/dim]")

    # ── KVM VMs ───────────────────────────────────────────────────
    vms = tree.add(f"[bold]KVM VMs[/bold]  {_src(F_HOSTS)}")
    for name, info in kvm_hosts(config).items():
        role = info.get("wg_role", "spoke")
        v = vms.add(
            f"[bold green]{name}[/bold green]  ({info.get('nickname', '')})  "
            f"[[dim]{role}[/dim]]"
        )
        v.add(f"virbr0 IP  : [cyan]{info.get('virbr0_ip', '—')}[/cyan]")
        v.add(f"WireGuard  : [cyan]{info.get('wg_ip', '—')}[/cyan]")
        v.add(f"Groups     : {', '.join(info.get('ansible_groups', []))}")
        v.add(f"Platform   : {info.get('platform', '—')}")

    # ── Controller ────────────────────────────────────────────────
    ctrl  = controller_info(config)
    ctree = tree.add(f"[bold]Controller (this host)[/bold]  {_src(F_HOSTS)}")
    ctree.add(f"WireGuard  : [cyan]{ctrl.get('wg_ip', '—')}[/cyan]  [spoke]")
    ctree.add(f"Nickname   : {ctrl.get('nickname', '${HOSTNAME}')}")
    ctree.add(f"Platform   : {ctrl.get('platform', '—')}")

    # ── SSH / Ansible ─────────────────────────────────────────────
    ssh = tree.add(f"[bold]SSH / Ansible[/bold]  {_src(F_KVM)}")
    ssh.add(f"User         : [cyan]{vm_user(config)}[/cyan]")
    ssh.add(f"SSH key      : [dim]{ssh_key_path(config)}[/dim]")
    ssh.add(f"Allowed IPs  : {', '.join(kvm_vars.get('allowed_ssh_ips', []))}")

    # ── Service Ports ─────────────────────────────────────────────
    ports = tree.add(f"[bold]Service Ports[/bold]  {_src(F_ALL)}")
    port_map = [
        ("Grafana",       "grafana_port"),
        ("Prometheus",    "prometheus_port"),
        ("Loki",          "loki_port"),
        ("Alertmanager",  "alertmanager_port"),
        ("node_exporter", "node_exporter_port"),
    ]
    for svc, key in port_map:
        ports.add(f"{svc:<14}: [cyan]{all_vars.get(key, '—')}[/cyan]")

    # ── Alert Profiles ────────────────────────────────────────────
    alerts = tree.add("[bold]Alert Profiles[/bold]")
    alerts.add(
        f"Default : {all_vars.get('alert_profile', '—')}"
        f"  {_src(F_ALL)}"
    )
    alerts.add(
        f"KVM lab : [cyan]drill[/cyan]"
        f"  {_src(F_LAB)}"
    )

    # ── System ────────────────────────────────────────────────────
    sys_node = tree.add(f"[bold]System[/bold]  {_src(F_ALL)}")
    sys_node.add(f"Timezone       : {all_vars.get('system_timezone', '—')}")
    sys_node.add(f"Locale         : {all_vars.get('system_locale', '—')}")
    sys_node.add(f"Docker Compose : {all_vars.get('docker_compose_version', '—')}")

    console.print(tree)

    # ── Service URL table ─────────────────────────────────────────
    hub = hub_vm(config)
    if hub:
        hub_ip = kvm_hosts(config)[hub].get("wg_ip", "")
        t = Table(
            title="Service URLs  (WireGuard access from controller)",
            header_style="bold cyan", box=box.SIMPLE,
        )
        t.add_column("Service")
        t.add_column("URL", style="cyan")
        t.add_row("Grafana",      f"http://{hub_ip}:{all_vars.get('grafana_port', 3000)}")
        t.add_row("Prometheus",   f"http://{hub_ip}:{all_vars.get('prometheus_port', 9090)}")
        t.add_row("Alertmanager", f"http://{hub_ip}:{all_vars.get('alertmanager_port', 9093)}")
        for name, info in kvm_hosts(config).items():
            if info.get("wg_role") == "spoke":
                wg_ip = info.get("wg_ip", "")
                t.add_row(
                    f"node_exporter ({name})",
                    f"http://{wg_ip}:{all_vars.get('node_exporter_port', 9100)}/metrics",
                )
        console.print()
        console.print(t)

    return 0


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ESACP unified lab management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", metavar="<subcommand>")
    sub.required = True

    sub.add_parser("confirmPrerequisites",
                   help="Check and install required host software")

    sub.add_parser("validateKeys",
                   help="Verify SOPS/age keys and WireGuard key structure")

    sub.add_parser("clearKnownHosts",
                   help="Remove stale SSH known_hosts entries for ESACP VMs")

    p = sub.add_parser("destroyVM",
                       help="Destroy a KVM VM and all its storage")
    p.add_argument("vm", help="VM name (e.g. dev01, dev02)")

    p = sub.add_parser("buildVM",
                       help="Build seed ISO, create VM, wait for autoinstall")
    p.add_argument("vm", help="VM name")

    p = sub.add_parser("provisionVM",
                       help="Run Ansible provisioning (task names and errors only)")
    p.add_argument("vm", help="VM name")
    p.add_argument("--check",               action="store_true", help="Ansible dry run")
    p.add_argument("--skip-fresh-snapshot", action="store_true",
                   help="Skip the 'Fresh Install' snapshot step")

    p = sub.add_parser("provision",
                       help="Full pipeline: create VM + provision + differentiate (stages 1–9)")
    p.add_argument("vm", help="VM name (e.g. dev01)")

    p = sub.add_parser("destroy",
                       help="Full teardown: VM + WireGuard + hosts_map + SOPS keys")
    p.add_argument("vm", help="VM name (e.g. dev01)")

    sub.add_parser("verifyVPN",
                   help="Test WireGuard connectivity and inter-VM routing")

    p = sub.add_parser("validateObservability",
                       help="Run the 27-check observability validation suite")
    p.add_argument("--verbose", "-v", action="store_true", help="Show passing check details")

    p = sub.add_parser("snapShotVM",
                       help="Create a snapshot or list snapshots for a VM")
    p.add_argument("vm",   help="VM name")
    p.add_argument("name", nargs="?", help="Snapshot name (omit to list existing snapshots)")

    sub.add_parser("displayConfiguration",
                   help="Show the lab configuration tree")

    args = parser.parse_args()

    try:
        config = load_config()
    except FileNotFoundError as exc:
        print(f"Config file not found: {exc}", file=sys.stderr)
        print("Run from the project root, or ensure hosts_map.yml exists.", file=sys.stderr)
        return 1

    # Validate VM arg for commands that require one
    vm_commands = {"destroyVM", "buildVM", "provisionVM", "provision", "destroy", "snapShotVM"}
    if args.command in vm_commands and hasattr(args, "vm"):
        valid = all_vm_names(config)
        if args.vm not in valid:
            console.print(f"[red]Unknown VM '{args.vm}'. Valid: {', '.join(valid)}[/red]")
            return 1

    dispatch = {
        "confirmPrerequisites":  cmd_confirm_prerequisites,
        "validateKeys":          cmd_validate_keys,
        "clearKnownHosts":       cmd_clear_known_hosts,
        "destroyVM":             cmd_destroy_vm,
        "buildVM":               cmd_build_vm,
        "provisionVM":           cmd_provision_vm,
        "provision":             cmd_provision,
        "destroy":               cmd_destroy,
        "verifyVPN":             cmd_verify_vpn,
        "validateObservability": cmd_validate_observability,
        "snapShotVM":            cmd_snapshot_vm,
        "displayConfiguration":  cmd_display_configuration,
    }

    return dispatch[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
