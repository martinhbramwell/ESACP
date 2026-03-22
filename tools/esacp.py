#!/usr/bin/env python3
"""
esacp — ESACP unified lab management CLI

10 subcommands for building, provisioning, and validating the ESACP KVM lab.
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
    verifyVPN                      Test WireGuard connectivity and inter-VM routing
    validateObservability          Run the 27-check observability validation suite
    snapShotVM <vm> [name]         Create or list snapshots for a VM
    displayConfiguration           Show the lab configuration tree
"""

import argparse
import getpass
import socket
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import yaml
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
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


def _tcp_port_open(host: str, port: int = 22, timeout: int = 5) -> bool:
    """Return True if a TCP connection to host:port succeeds. No SSH, no known_hosts."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def _populate_known_hosts(entries: list) -> None:
    """
    Run ssh-keyscan for each entry and append the results to ~/.ssh/known_hosts.
    Entries that time out (host not yet reachable) are silently skipped.
    Called after _remove_known_hosts so we always write the current key.
    """
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    for entry in entries:
        result = subprocess.run(
            ["ssh-keyscan", "-H", "-T", "5", entry],
            capture_output=True, text=True,
        )
        if result.stdout.strip():
            with open(known_hosts, "a") as fh:
                fh.write(result.stdout)
            console.print(f"  [dim]ssh-keyscan: key added for {entry}[/dim]")


def wait_for_poweroff(vm: str, timeout: int = 1800) -> bool:
    console.print("  [dim]VM powers off automatically when installation finishes (~10–20 min)[/dim]")
    start = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Autoinstall running... ({task.fields[elapsed]}s)[/cyan]"),
        transient=True,
    ) as progress:
        task = progress.add_task("wait", elapsed=0)
        while time.time() - start < timeout:
            if vm_state(vm) == "shut off":
                console.print(f"[green]✅  Autoinstall complete ({int(time.time()-start)}s)[/green]")
                return True
            progress.update(task, elapsed=int(time.time() - start))
            time.sleep(10)
    console.print(f"[red]❌  Autoinstall did not complete within {timeout // 60} min[/red]")
    return False


def wait_for_ssh(vm: str, config: dict, timeout: int = 120) -> bool:
    start = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Polling SSH... ({task.fields[elapsed]}s / {task.fields[timeout]}s)[/cyan]"),
        transient=True,
    ) as progress:
        task = progress.add_task("ssh", elapsed=0, timeout=timeout)
        while time.time() - start < timeout:
            if ansible_ping(vm, config):
                console.print("[green]✅  SSH available[/green]")
                return True
            progress.update(task, elapsed=int(time.time() - start))
            time.sleep(5)
    console.print(f"[red]❌  SSH timeout after {timeout}s[/red]")
    return False


# ── 1. confirmPrerequisites ────────────────────────────────────────────────────

# (tool, apt-package, install-method: "apt" | "manual")
REQUIRED_TOOLS = [
    ("virsh",            "libvirt-clients",   "apt"),
    ("virt-install",     "virtinst",          "apt"),
    ("cloud-localds",    "cloud-image-utils", "apt"),
    ("ansible",          "ansible",           "apt"),
    ("ansible-playbook", "ansible",           "apt"),
    ("wg",               "wireguard-tools",   "apt"),
    ("python3",          "python3",           "apt"),
    ("ssh-keygen",       "openssh-client",    "apt"),
    ("sops",             "sops",              "manual"),
    ("age",              "age",               "manual"),
    ("age-keygen",       "age",               "manual"),
]

MANUAL_INSTALL_HINTS = {
    "sops": (
        "https://github.com/getsops/sops/releases\n"
        "  sudo mv sops-v*.linux.amd64 /usr/local/bin/sops && sudo chmod +x /usr/local/bin/sops"
    ),
    "age": (
        "https://github.com/FiloSottile/age/releases\n"
        "  sudo tar xf age-v*.tar.gz -C /tmp && sudo cp /tmp/age/age /tmp/age/age-keygen /usr/local/bin/"
    ),
}


def cmd_confirm_prerequisites(args, config: dict) -> int:
    banner("Confirm Prerequisites")

    table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
    table.add_column("Tool",    style="cyan",  min_width=18)
    table.add_column("Package", min_width=18)
    table.add_column("Status",  min_width=12)

    missing_apt: set = set()
    missing_manual: list = []
    seen_packages: set = set()

    for tool, pkg, method in REQUIRED_TOOLS:
        found = shutil.which(tool) is not None
        status = "[green]✓ found[/green]" if found else "[red]✗ missing[/red]"
        table.add_row(tool, pkg, status)
        if not found:
            if method == "apt" and pkg not in seen_packages:
                missing_apt.add(pkg)
                seen_packages.add(pkg)
            elif method == "manual" and pkg not in seen_packages:
                missing_manual.append((tool, pkg))
                seen_packages.add(pkg)

    console.print(table)

    # Required files
    console.print()
    age_key    = Path(os.path.expanduser("~/.config/sops/age/keys.txt"))
    sops_yaml  = PROJECT_ROOT / ".sops.yaml"
    ssh_key    = Path(ssh_key_path(config))
    ssh_pub    = Path(str(ssh_key) + ".pub")

    file_checks = [
        (age_key,   "age decryption key"),
        (sops_yaml, "SOPS config (.sops.yaml)"),
        (ssh_key,   f"SSH private key ({ssh_key.name})"),
        (ssh_pub,   f"SSH public key ({ssh_key.name}.pub)"),
    ]
    file_issues = []
    for path, desc in file_checks:
        exists = path.exists()
        icon   = "[green]✓[/green]" if exists else "[red]✗[/red]"
        console.print(f"  {icon} {desc}: [dim]{path}[/dim]")
        if not exists:
            file_issues.append((path, desc))

    console.print()

    if not missing_apt and not missing_manual and not file_issues:
        console.print("[green]✅  All prerequisites satisfied.[/green]")
        return 0

    # Offer apt install
    if missing_apt:
        pkgs = " ".join(sorted(missing_apt))
        console.print(f"[yellow]Missing apt packages:[/yellow] {pkgs}")
        if confirm("Install now via apt?"):
            result = subprocess.run(["sudo", "apt", "install", "-y"] + sorted(missing_apt))
            if result.returncode != 0:
                console.print("[red]❌  apt install failed.[/red]")
                return 1
            console.print("[green]✅  Packages installed.[/green]")
        else:
            console.print(f"[dim]Re-run after: sudo apt install -y {pkgs}[/dim]")

    # Manual installs
    if missing_manual:
        console.print()
        console.print("[yellow]Manual installs required:[/yellow]")
        reported = set()
        for tool, pkg in missing_manual:
            if pkg not in reported:
                hint = MANUAL_INSTALL_HINTS.get(tool, MANUAL_INSTALL_HINTS.get(pkg, ""))
                console.print(f"  [cyan]{pkg}[/cyan]: {hint}")
                reported.add(pkg)

    # File issues
    if file_issues:
        console.print()
        console.print("[yellow]Missing files:[/yellow]")
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

    return 1 if (missing_manual or file_issues) else 0


# ── 2. validateKeys ────────────────────────────────────────────────────────────

def cmd_validate_keys(args, config: dict) -> int:
    banner("Validate Keys")

    age_key  = Path(os.path.expanduser("~/.config/sops/age/keys.txt"))
    sops_yml = PROJECT_ROOT / ".sops.yaml"
    keys_enc = PROJECT_ROOT / "config" / "wireguard" / "keys.sops.yml"

    errors = []

    for path, label in [(age_key, "age key"), (sops_yml, ".sops.yaml"), (keys_enc, "keys.sops.yml")]:
        if path.exists():
            console.print(f"  [green]✓[/green] {label}: [dim]{path}[/dim]")
        else:
            console.print(f"  [red]✗[/red] {label}: [dim]{path}[/dim]")
            errors.append(f"Missing: {path}")

    if errors:
        for e in errors:
            console.print(f"[red]❌  {e}[/red]")
        return 1

    console.print()
    console.print("[cyan]Attempting SOPS decryption...[/cyan]")
    result = subprocess.run(["sops", "-d", str(keys_enc)], capture_output=True, text=True)

    if result.returncode != 0:
        console.print(f"[red]❌  SOPS decryption failed:[/red]")
        console.print(f"[red]   {result.stderr.strip()}[/red]")
        return 1

    try:
        decrypted = yaml.safe_load(result.stdout)
    except yaml.YAMLError as exc:
        console.print(f"[red]❌  YAML parse error: {exc}[/red]")
        return 1

    expected_hosts = list(kvm_hosts(config).keys()) + ["controller"]
    ok = True
    for host in expected_hosts:
        block = decrypted.get(host, {})
        has_priv = "private_key" in block
        has_pub  = "public_key"  in block
        icon = "[green]✓[/green]" if (has_priv and has_pub) else "[red]✗[/red]"
        console.print(f"  {icon} {host}: private_key + public_key")
        if not (has_priv and has_pub):
            ok = False

    psks = decrypted.get("preshared_keys", {})
    for psk_key in ["controller_saconsole", "target1_saconsole"]:
        icon = "[green]✓[/green]" if psk_key in psks else "[red]✗[/red]"
        console.print(f"  {icon} preshared_key: {psk_key}")
        if psk_key not in psks:
            ok = False

    console.print()
    if ok:
        console.print("[green]✅  All WireGuard keys present and decryptable.[/green]")
        return 0
    else:
        console.print("[red]❌  Key structure incomplete — re-run config/wireguard/generate_keys.sh[/red]")
        return 1


# ── 3. clearKnownHosts ────────────────────────────────────────────────────────

def _known_hosts_entries(info: dict) -> list:
    """All SSH known_hosts identifiers for one host (hostname, nickname, IPs)."""
    seen = []
    for field in ("hostname", "nickname", "virbr0_ip", "wg_ip"):
        val = info.get(field)
        if val and val not in seen:
            seen.append(val)
    return seen


def _remove_known_hosts(entries: list) -> int:
    """Remove a list of entries from ~/.ssh/known_hosts. Returns count removed."""
    removed = 0
    for entry in entries:
        result = subprocess.run(["ssh-keygen", "-R", entry], capture_output=True, text=True)
        if result.returncode == 0 and "not found" not in result.stderr:
            removed += 1
    return removed


def cmd_clear_known_hosts(args, config: dict) -> int:
    banner("Clear Known Hosts")

    all_entries = []
    for name, info in kvm_hosts(config).items():
        for e in _known_hosts_entries(info):
            if e not in all_entries:
                all_entries.append(e)

    console.print(f"Removing up to {len(all_entries)} entries from ~/.ssh/known_hosts:")
    for entry in all_entries:
        console.print(f"  [dim]{entry}[/dim]")
    console.print()

    removed = _remove_known_hosts(all_entries)
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

# Toshiba remote hypervisor constants (see CLAUDE.md — Stage 2.2)
TOSHIBA_SSH_ALIAS  = "toshiba"
TOSHIBA_USER       = "hasan"
TOSHIBA_IMAGES_DIR = "/mnt/esacp-disk/var/lib/libvirt/images"
TOSHIBA_UBUNTU_ISO = f"{TOSHIBA_IMAGES_DIR}/ubuntu-24.04.4-live-server-amd64.iso"
TOSHIBA_POOL       = "esacp"


def _toshiba_vm_exists(vm: str) -> bool:
    return subprocess.run(
        ["ssh", TOSHIBA_SSH_ALIAS, "virsh", "--connect", "qemu:///system", "dominfo", vm],
        capture_output=True,
    ).returncode == 0


def _toshiba_vm_state(vm: str) -> Optional[str]:
    r = subprocess.run(
        ["ssh", TOSHIBA_SSH_ALIAS, "virsh", "--connect", "qemu:///system", "domstate", vm],
        capture_output=True, text=True,
    )
    return r.stdout.strip().lower() if r.returncode == 0 else None


def _toshiba_tcp_probe(virbr0_ip: str) -> bool:
    """Probe TCP port 22 on a toshiba-internal IP via ProxyJump — no known_hosts check."""
    r = subprocess.run(
        ["ssh",
         "-o", "ConnectTimeout=5",
         "-o", "StrictHostKeyChecking=no",
         "-o", "BatchMode=yes",
         "-J", f"{TOSHIBA_USER}@{TOSHIBA_SSH_ALIAS}",
         f"you@{virbr0_ip}", "true"],
        capture_output=True,
    )
    return r.returncode == 0


def _toshiba_add_known_hosts(virbr0_ip: str) -> None:
    """Collect the host key via toshiba and append it to local known_hosts."""
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    # ssh-keyscan via ProxyJump: run keyscan from toshiba, capture output locally
    r = subprocess.run(
        ["ssh", TOSHIBA_SSH_ALIAS, "ssh-keyscan", "-H", "-T", "5", virbr0_ip],
        capture_output=True, text=True,
    )
    if r.stdout.strip():
        with open(known_hosts, "a") as fh:
            fh.write(r.stdout)
        console.print(f"  [dim]Host key for {virbr0_ip} added to known_hosts[/dim]")


def _build_vm_toshiba(vm: str, vm_info: dict, config: dict) -> int:
    """Build a VM on the toshiba remote hypervisor."""
    virbr0_ip   = vm_info.get("virbr0_ip", "")
    ram         = 4096 if vm == "saconsole" else 2048
    remote_seed = f"{TOSHIBA_IMAGES_DIR}/{vm}-seed.iso"

    vm_exists = _toshiba_vm_exists(vm)

    # ── Steps 1 & 2: Seed ISO + VM creation ──────────────────────────────────
    if vm_exists:
        console.print(f"[bold]Steps 1–2:[/bold] Seed ISO + VM creation")
        console.print(f"  [green]✓[/green] VM already exists on toshiba — skipping")
    else:
        # Step 1 — Seed ISO (build locally if needed, then scp to toshiba)
        console.print("[bold]Step 1/4:[/bold] Seed ISO")
        seed_local = PLATFORMS_KVM / f"{vm}-seed.iso"
        if seed_local.exists():
            console.print(f"  [green]✓[/green] {seed_local.name} already built locally")
        else:
            if not _build_seed_iso_local(vm):
                return 1

        console.print(f"  Uploading seed ISO to toshiba:{TOSHIBA_IMAGES_DIR}/...")
        r = subprocess.run(
            ["scp", str(seed_local), f"{TOSHIBA_USER}@{TOSHIBA_SSH_ALIAS}:{remote_seed}"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            console.print(f"[red]❌  scp failed: {r.stderr.strip()}[/red]")
            return 1
        console.print(f"  [green]✓[/green] Seed ISO uploaded")

        # Step 2 — Create VM on toshiba via SSH
        console.print()
        console.print("[bold]Step 2/4:[/bold] Create VM on toshiba")
        virt_cmd = (
            f"virt-install --connect qemu:///system"
            f" --name {vm}"
            f" --ram {ram}"
            f" --vcpus 2"
            f" --disk pool={TOSHIBA_POOL},size=20,format=qcow2"
            f" --location '{TOSHIBA_UBUNTU_ISO},kernel=casper/vmlinuz,initrd=casper/initrd'"
            f" --disk path={remote_seed},device=cdrom,readonly=on"
            f" --network network=default"
            f" --os-variant ubuntu20.04"
            f" --extra-args 'autoinstall ds=nocloud'"
            f" --graphics vnc"
            f" --noautoconsole"
        )
        r = subprocess.run(
            ["ssh", TOSHIBA_SSH_ALIAS, virt_cmd],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            console.print(f"[red]❌  virt-install on toshiba failed:\n{r.stderr.strip()}[/red]")
            return 1
        console.print(f"  [green]✓[/green] {vm} created on toshiba, autoinstall in progress")

    # ── Step 3: Clear stale known_hosts ──────────────────────────────────────
    console.print()
    console.print("[bold]Step 3/4:[/bold] Clear stale known_hosts entries")
    entries = _known_hosts_entries(vm_info)
    removed = _remove_known_hosts(entries)
    if removed:
        console.print(f"  [green]✓[/green] Cleared {removed} stale entry/entries")
    else:
        console.print(f"  [dim]No stale entries found[/dim]")

    # ── Step 4: Wait for SSH via ProxyJump ───────────────────────────────────
    console.print()
    console.print("[bold]Step 4/4:[/bold] Ensure VM is running and SSH-ready (via ProxyJump)")

    if not virbr0_ip:
        console.print("[red]❌  No virbr0_ip in host config — cannot poll[/red]")
        return 1

    state = _toshiba_vm_state(vm)
    console.print(f"  Current state: [cyan]{state or 'unknown'}[/cyan]")
    if not state:
        console.print(f"[red]❌  Could not determine VM state on toshiba[/red]")
        return 1
    if state not in ("running", "shut off"):
        console.print(f"[red]❌  Unexpected VM state: {state!r}[/red]")
        return 1
    if state == "shut off":
        console.print(f"  Starting {vm} on toshiba...")
        subprocess.run(
            ["ssh", TOSHIBA_SSH_ALIAS,
             "virsh", "--connect", "qemu:///system", "start", vm],
            check=True,
        )

    console.print(f"  [dim]Polling {virbr0_ip} via ProxyJump through toshiba...[/dim]")
    poll_start   = time.time()
    poll_timeout = 1800
    powered_off  = False

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Waiting for SSH or autoinstall completion... ({task.fields[elapsed]}s)[/cyan]"),
        transient=True,
    ) as progress:
        task = progress.add_task("wait", elapsed=0)
        while time.time() - poll_start < poll_timeout:
            if _toshiba_vm_state(vm) == "shut off":
                powered_off = True
                break
            if _toshiba_tcp_probe(virbr0_ip):
                break
            progress.update(task, elapsed=int(time.time() - poll_start))
            time.sleep(10)
        else:
            console.print(f"[red]❌  Timed out after {poll_timeout // 60} min[/red]")
            return 1

    elapsed = int(time.time() - poll_start)

    if powered_off:
        console.print(f"  [green]✓[/green] Autoinstall complete ({elapsed}s) — starting {vm}")
        subprocess.run(
            ["ssh", TOSHIBA_SSH_ALIAS,
             "virsh", "--connect", "qemu:///system", "start", vm],
            check=True,
        )
        console.print(f"  [dim]Waiting for SSH after reboot...[/dim]")
        reboot_start = time.time()
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Waiting for SSH... ({task.fields[elapsed]}s)[/cyan]"),
            transient=True,
        ) as progress:
            task = progress.add_task("ssh", elapsed=0)
            while time.time() - reboot_start < 300:
                if _toshiba_tcp_probe(virbr0_ip):
                    break
                progress.update(task, elapsed=int(time.time() - reboot_start))
                time.sleep(5)
            else:
                console.print("[red]❌  SSH did not come up within 5 min after reboot[/red]")
                return 1
    else:
        console.print(f"  [green]✓[/green] TCP port 22 open ({elapsed}s)")

    # Populate known_hosts so Ansible can connect
    console.print(f"  Updating known_hosts via toshiba keyscan...")
    _toshiba_add_known_hosts(virbr0_ip)

    # Ansible ping to confirm
    console.print(f"  Confirming Ansible connectivity...")
    for attempt in range(6):
        if ansible_ping(vm, config):
            break
        time.sleep(5)
    else:
        console.print(f"[red]❌  Ansible cannot reach {vm}[/red]")
        console.print(f"    Check: ansible user '{vm_user(config)}', key '{ssh_key_path(config)}'")
        return 1

    console.print()
    console.print(f"[green]✅  {vm} is built on toshiba and SSH-ready.[/green]")
    console.print(f"    Next: [cyan]python tools/esacp.py provisionVM {vm}[/cyan]")
    return 0


def _virsh_vol_upload(seed_local: Path, vm: str) -> bool:
    """Upload seed ISO into the default libvirt pool via virsh — no sudo needed."""
    iso_name = f"{vm}-seed.iso"
    size     = seed_local.stat().st_size

    # Remove stale volume if present (ignore failure)
    subprocess.run(
        ["virsh", "vol-delete", iso_name, "--pool", "default"],
        capture_output=True,
    )

    result = subprocess.run(
        ["virsh", "vol-create-as", "default", iso_name, str(size), "--format", "raw"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]❌  vol-create-as failed: {result.stderr.strip()}[/red]")
        return False

    result = subprocess.run(
        ["virsh", "vol-upload", "--pool", "default", iso_name, str(seed_local)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]❌  vol-upload failed: {result.stderr.strip()}[/red]")
        return False

    console.print(f"  [green]✓[/green] {iso_name} uploaded to default pool")
    return True


def _build_seed_iso_local(vm: str) -> bool:
    """Build the seed ISO locally (platforms/kvm/<vm>-seed.iso). No upload."""
    cloud_init = PLATFORMS_KVM / "cloud-init" / vm
    user_data  = cloud_init / "user-data"
    meta_data  = cloud_init / "meta-data"
    for f in (user_data, meta_data):
        if not f.exists():
            console.print(f"[red]❌  Missing cloud-init file: {f}[/red]")
            return False

    seed_local = PLATFORMS_KVM / f"{vm}-seed.iso"
    console.print(f"  Building {vm}-seed.iso...")
    result = subprocess.run(
        ["cloud-localds", str(seed_local), str(user_data), str(meta_data)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]❌  cloud-localds failed: {result.stderr.strip()}[/red]")
        return False
    console.print(f"  [green]✓[/green] {vm}-seed.iso built")
    return True


def _build_seed_iso(vm: str) -> bool:
    """Build seed ISO and upload it into the local default libvirt pool."""
    if not _build_seed_iso_local(vm):
        return False
    seed_local = PLATFORMS_KVM / f"{vm}-seed.iso"
    console.print(f"  Uploading seed ISO to default libvirt pool...")
    if not _virsh_vol_upload(seed_local, vm):
        return False
    console.print(f"  [green]✓[/green] {vm}-seed.iso ready at {IMAGES_DIR / (vm + '-seed.iso')}")
    return True


def _create_vm(vm: str, config: dict) -> bool:
    if subprocess.run(["virsh", "dominfo", vm], capture_output=True).returncode == 0:
        console.print(f"  [yellow]VM '{vm}' already exists — skipping virt-install.[/yellow]")
        return True

    iso_symlink = PROJECT_ROOT / "ubuntu-24.04.4-live-server-amd64.iso"
    try:
        iso_real = subprocess.run(
            ["readlink", "-f", str(iso_symlink)], capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        iso_real = str(iso_symlink)

    if not Path(iso_real).exists():
        console.print(f"[red]❌  ISO not found: {iso_real}[/red]")
        return False

    seed  = IMAGES_DIR / f"{vm}-seed.iso"
    disk  = IMAGES_DIR / f"{vm}.qcow2"
    ram   = 4096 if vm == "saconsole" else 2048
    vcpus = 2

    cmd = [
        "virt-install",
        "--name", vm,
        "--ram",  str(ram),
        "--vcpus", str(vcpus),
        "--disk", f"path={disk},size=20,format=qcow2",
        "--location", f"{iso_real},kernel=casper/vmlinuz,initrd=casper/initrd",
        "--disk", f"path={seed},device=cdrom,readonly=on",
        "--network", "network=default",
        "--os-variant", "ubuntu24.04",
        "--extra-args", "autoinstall ds=nocloud",
        "--graphics", "vnc",
        "--noautoconsole",
    ]

    console.print(f"  Running virt-install for {vm}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]❌  virt-install failed:\n{result.stderr.strip()}[/red]")
        return False

    console.print(f"  [green]✓[/green] {vm} created, autoinstall in progress")
    return True


def cmd_build_vm(args, config: dict) -> int:
    """
    Idempotent: interrogates actual KVM/VM state at every step and skips
    what is already done.

    Decision tree
    ─────────────
    VM does not exist
      └─ Seed ISO in /var/lib/libvirt/images/?  → skip cloud-localds + copy
           Seed ISO built locally?              → skip cloud-localds, just copy
           Neither                             → build and copy
         then virt-install → autoinstall runs in background

    VM exists
      └─ skip seed ISO and virt-install entirely

    Either path continues:
      Clear known_hosts for this VM (fresh install always has a new host key)

      running + SSH up within 30 s  → already done, exit 0
      running + no SSH after 30 s   → autoinstall in progress
                                      wait for poweroff → start
      shut off                      → start
      any other state               → error
      then wait for SSH
    """
    vm      = args.vm
    vm_info = kvm_hosts(config).get(vm, {})
    banner(f"Build VM: {vm}")

    hypervisor = vm_info.get("hypervisor", "local")
    if hypervisor == "toshiba":
        return _build_vm_toshiba(vm, vm_info, config)

    vm_exists = subprocess.run(["virsh", "dominfo", vm], capture_output=True).returncode == 0

    # ── Steps 1 & 2: Seed ISO + VM creation ──────────────────────────────────
    if vm_exists:
        console.print(f"[bold]Steps 1–2:[/bold] Seed ISO + VM creation")
        console.print(f"  [green]✓[/green] VM already exists — skipping")
    else:
        # Step 1 — Seed ISO
        console.print("[bold]Step 1/4:[/bold] Seed ISO")
        seed_dest  = IMAGES_DIR / f"{vm}-seed.iso"
        seed_local = PLATFORMS_KVM / f"{vm}-seed.iso"

        if seed_dest.exists():
            console.print(f"  [green]✓[/green] {seed_dest} already present — skipping build")
        elif seed_local.exists():
            console.print(f"  Seed ISO built — uploading to default libvirt pool...")
            if not _virsh_vol_upload(seed_local, vm):
                return 1
        else:
            if not _build_seed_iso(vm):
                return 1

        # Step 2 — Create VM
        console.print()
        console.print("[bold]Step 2/4:[/bold] Create VM")
        if not _create_vm(vm, config):
            return 1

    # ── Step 3: Clear stale known_hosts ──────────────────────────────────────
    # A freshly installed or rebuilt VM always has a new host key.  Stale
    # entries in known_hosts will prevent Ansible from connecting.
    console.print()
    console.print("[bold]Step 3/4:[/bold] Clear stale known_hosts entries")
    entries = _known_hosts_entries(vm_info)
    removed = _remove_known_hosts(entries)
    if removed:
        console.print(f"  [green]✓[/green] Cleared {removed} stale entry/entries: {', '.join(entries[:removed])}")
    else:
        console.print(f"  [dim]No stale entries found[/dim]")

    # ── Step 4: Ensure VM is running, then wait for SSH ──────────────────────
    console.print()
    console.print("[bold]Step 4/4:[/bold] Ensure VM is running and SSH-ready")

    virbr0_ip = vm_info.get("virbr0_ip", "")

    state = vm_state(vm)
    console.print(f"  Current state: [cyan]{state or 'unknown'}[/cyan]")

    if not state:
        console.print(f"[red]❌  Could not determine state of {vm} — is libvirt running?[/red]")
        return 1

    if state not in ("running", "shut off"):
        console.print(f"[red]❌  Unexpected VM state: {state!r}[/red]")
        return 1

    if state == "shut off":
        console.print(f"  Starting {vm}...")
        subprocess.run(["virsh", "start", vm], check=True)

    # Poll for TCP port 22 OR poweroff.  Using TCP (not Ansible) avoids known_hosts
    # entirely and correctly handles both autoinstall (→ poweroff) and slow boot
    # (→ SSH eventually comes up without powering off).
    console.print(f"  [dim]Polling TCP port 22 on {virbr0_ip or vm} (or watching for poweroff)...[/dim]")
    poll_start   = time.time()
    poll_timeout = 1800  # 30 min max (covers full autoinstall)
    powered_off  = False

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Waiting for SSH or autoinstall completion... ({task.fields[elapsed]}s)[/cyan]"),
        transient=True,
    ) as progress:
        task = progress.add_task("wait", elapsed=0)
        while time.time() - poll_start < poll_timeout:
            current_state = vm_state(vm)
            if current_state == "shut off":
                powered_off = True
                break
            if virbr0_ip and _tcp_port_open(virbr0_ip):
                break
            progress.update(task, elapsed=int(time.time() - poll_start))
            time.sleep(10)
        else:
            console.print(f"[red]❌  Timed out after {poll_timeout // 60} min[/red]")
            return 1

    elapsed = int(time.time() - poll_start)

    if powered_off:
        console.print(f"  [green]✓[/green] Autoinstall complete ({elapsed}s) — starting {vm}")
        subprocess.run(["virsh", "start", vm], check=True)
        # Now poll again for TCP after the reboot
        console.print(f"  [dim]Waiting for SSH after reboot...[/dim]")
        reboot_start = time.time()
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Waiting for SSH... ({task.fields[elapsed]}s)[/cyan]"),
            transient=True,
        ) as progress:
            task = progress.add_task("ssh", elapsed=0)
            while time.time() - reboot_start < 300:
                if virbr0_ip and _tcp_port_open(virbr0_ip):
                    break
                progress.update(task, elapsed=int(time.time() - reboot_start))
                time.sleep(5)
            else:
                console.print("[red]❌  SSH did not come up within 5 min after reboot[/red]")
                return 1
    else:
        console.print(f"  [green]✓[/green] TCP port 22 open ({elapsed}s)")

    # TCP is open — now fix known_hosts so Ansible can connect without prompts.
    # Clear stale entries and replace with the current host key via ssh-keyscan.
    console.print(f"  Updating known_hosts with current host key...")
    _remove_known_hosts(_known_hosts_entries(vm_info))
    _populate_known_hosts([virbr0_ip] if virbr0_ip else [vm])

    # Final confirmation via Ansible ping
    console.print(f"  Confirming Ansible connectivity...")
    for attempt in range(6):
        if ansible_ping(vm, config):
            break
        time.sleep(5)
    else:
        console.print(f"[red]❌  Ansible cannot reach {vm} even though TCP port 22 is open[/red]")
        console.print(f"    Check: ansible user '{vm_user(config)}', key '{ssh_key_path(config)}'")
        return 1

    console.print()
    console.print(f"[green]✅  {vm} is built and SSH-ready.[/green]")
    console.print(f"    Next: [cyan]python tools/esacp.py provisionVM {vm}[/cyan]")
    return 0


# ── 6. provisionVM ────────────────────────────────────────────────────────────

def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _filter_ansible_line(line: str, state: dict) -> Optional[str]:
    """
    Given a raw ansible-playbook output line, return a formatted string to
    display or None to suppress it. `state` carries context between calls.
    """
    clean = _strip_ansi(line)

    if clean.startswith("PLAY RECAP"):
        state["in_recap"] = True
        return f"\n[bold cyan]{clean}[/bold cyan]"

    if state.get("in_recap"):
        # PLAY RECAP summary line: "saconsole : ok=77  changed=11 ..."
        if re.match(r"\w[\w.\-]+\s*:", clean):
            return f"  [dim]{clean}[/dim]"
        return None

    if clean.startswith("PLAY ["):
        state["current_task"] = ""
        return f"\n[bold cyan]{clean}[/bold cyan]"

    if clean.startswith("TASK ["):
        m = re.match(r"TASK \[(.+?)\]", clean)
        state["current_task"] = m.group(1).strip() if m else clean
        state["task_printed"] = False
        return None  # hold until we see the result

    if clean.startswith("ok:"):
        task = state.get("current_task", "")
        return f"  [green]✓[/green] {task}"

    if clean.startswith("changed:"):
        task = state.get("current_task", "")
        return f"  [yellow]★[/yellow] {task} [yellow](changed)[/yellow]"

    if clean.startswith("skipping:"):
        return None

    if "fatal:" in clean or "FAILED!" in clean or clean.startswith("UNREACHABLE!"):
        return f"[red]❌  {clean}[/red]"

    # Detail lines after a fatal (indented msg/stderr/stdout)
    if state.get("current_task") and re.match(r"\s+(msg|stderr|stdout|reason):", clean):
        return f"[red]{clean}[/red]"

    return None


def _virsh_snapshot_list(vm: str, hypervisor: str) -> list[str]:
    """Return snapshot names for a VM, routing to the correct hypervisor."""
    if hypervisor == "toshiba":
        cmd = ["ssh", TOSHIBA_SSH_ALIAS,
               f"virsh --connect qemu:///system snapshot-list {vm} --name"]
    else:
        cmd = ["virsh", "snapshot-list", vm, "--name"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip().splitlines() if r.returncode == 0 else []


def _virsh_snapshot_create(vm: str, name: str, hypervisor: str) -> bool:
    """Take a snapshot, routing to the correct hypervisor. Returns True on success."""
    if hypervisor == "toshiba":
        cmd = ["ssh", TOSHIBA_SSH_ALIAS,
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
        formatted = _filter_ansible_line(raw_line.rstrip(), filter_state)
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


# ── 7. verifyVPN ──────────────────────────────────────────────────────────────

def cmd_verify_vpn(args, config: dict) -> int:
    banner("Verify WireGuard VPN")

    hosts = kvm_hosts(config)
    user  = vm_user(config)
    key   = ssh_key_path(config)
    all_ok = True

    # 1. Controller → each VM's WireGuard IP
    console.print("[bold]Controller → VM (ping):[/bold]")
    for name, info in hosts.items():
        wg_ip = info.get("wg_ip")
        if not wg_ip:
            continue
        result = subprocess.run(
            ["ping", "-c", "3", "-W", "2", wg_ip],
            capture_output=True, text=True,
        )
        ok   = result.returncode == 0
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        console.print(f"  {icon} ping {name} ({wg_ip})")
        if ok:
            # Extract RTT from last line
            for line in result.stdout.splitlines():
                if "rtt" in line or "round-trip" in line:
                    console.print(f"    [dim]{line.strip()}[/dim]")
        all_ok = all_ok and ok

    # 2. WireGuard status on hub
    console.print()
    hub = hub_vm(config)
    if hub:
        hub_ip = hosts[hub].get("wg_ip")
        console.print(f"[bold]WireGuard peers on {hub} (sudo wg show):[/bold]")
        result = ssh_run(hub_ip, user, key, "sudo wg show")
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                console.print(f"  [dim]{line}[/dim]")
        else:
            console.print(f"  [red]SSH failed: {result.stderr.strip()}[/red]")
            all_ok = False

    # 3. Cross-VM pings (each VM → each other VM)
    console.print()
    console.print("[bold]Cross-VM ping (via WireGuard):[/bold]")
    vm_list = list(hosts.items())
    for src_name, src_info in vm_list:
        src_ip = src_info.get("wg_ip")
        if not src_ip:
            continue
        for dst_name, dst_info in vm_list:
            if src_name == dst_name:
                continue
            dst_ip = dst_info.get("wg_ip")
            if not dst_ip:
                continue
            result = ssh_run(src_ip, user, key, f"ping -c 1 -W 2 {dst_ip}")
            ok   = result.returncode == 0
            icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            console.print(f"  {icon} {src_name} → {dst_name} ({dst_ip})")
            all_ok = all_ok and ok

    console.print()
    if all_ok:
        console.print("[green]✅  All WireGuard connectivity checks passed.[/green]")
    else:
        console.print("[red]❌  Some connectivity checks failed.[/red]")
    return 0 if all_ok else 1


# ── 8. validateObservability ──────────────────────────────────────────────────

def _get_grafana_creds(config: dict) -> tuple:
    user     = os.environ.get("GRAFANA_ADMIN_USER", "admin")
    password = os.environ.get("GRAFANA_ADMIN_PASSWORD", "")

    if password:
        console.print("  [dim]Grafana credentials from environment[/dim]")
        return user, password

    # Try reading from saconsole's .env file
    hub = hub_vm(config)
    if hub:
        hub_ip = kvm_hosts(config)[hub].get("wg_ip")
        result = ssh_run(hub_ip, vm_user(config), ssh_key_path(config),
                         "sudo grep GRAFANA_ADMIN_PASSWORD /opt/observability/.env 2>/dev/null")
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "GRAFANA_ADMIN_PASSWORD=" in line:
                    password = line.split("=", 1)[1].strip()
                    console.print(f"  [dim]Grafana credentials retrieved from {hub}[/dim]")
                    return user, password

    console.print("[yellow]Grafana password not found in env or on saconsole.[/yellow]")
    password = getpass.getpass("Grafana admin password: ")
    return user, password


def cmd_validate_observability(args, config: dict) -> int:
    banner("Validate Observability")

    script = PROJECT_ROOT / "orchestration" / "validate_observability.py"
    if not script.exists():
        console.print(f"[red]❌  Script not found: {script}[/red]")
        return 1

    console.print("Retrieving Grafana credentials...")
    user, password = _get_grafana_creds(config)

    env = os.environ.copy()
    env["GRAFANA_ADMIN_USER"]     = user
    env["GRAFANA_ADMIN_PASSWORD"] = password

    cmd = ["python3", str(script)]
    if args.verbose:
        cmd.append("--verbose")

    result = subprocess.run(cmd, env=env)
    return result.returncode


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
    for label, key in [
        ("controller", "wg_pubkey_controller"),
        ("saconsole",  "wg_pubkey_saconsole"),
        ("target1",    "wg_pubkey_target1"),
    ]:
        val = all_vars.get(key, "—")
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
    p.add_argument("vm", help="VM name (e.g. saconsole, target1)")

    p = sub.add_parser("buildVM",
                       help="Build seed ISO, create VM, wait for autoinstall")
    p.add_argument("vm", help="VM name")

    p = sub.add_parser("provisionVM",
                       help="Run Ansible provisioning (task names and errors only)")
    p.add_argument("vm", help="VM name")
    p.add_argument("--check",               action="store_true", help="Ansible dry run")
    p.add_argument("--skip-fresh-snapshot", action="store_true",
                   help="Skip the 'Fresh Install' snapshot step")

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
    vm_commands = {"destroyVM", "buildVM", "provisionVM", "snapShotVM"}
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
        "verifyVPN":             cmd_verify_vpn,
        "validateObservability": cmd_validate_observability,
        "snapShotVM":            cmd_snapshot_vm,
        "displayConfiguration":  cmd_display_configuration,
    }

    return dispatch[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
