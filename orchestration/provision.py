#!/usr/bin/env python3
"""
ESACP Provisioning Orchestrator
Manages VM lifecycle and Ansible provisioning

Usage:
    python3 provision.py --target dev                # Provision dev VM
    python3 provision.py --target dev --revert       # Revert to baseline first
    python3 provision.py --target dev --check        # Dry run
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
ANSIBLE_DIR = PROJECT_ROOT / "ansible"
ORCHESTRATION_DIR = PROJECT_ROOT / "orchestration"

# VM configurations
# DEV_VM_HOSTNAME and SNAPSHOT_NAME are read from environment variables so they
# match the values set in the operator's shell session (see SETUP_GUIDE.md).
# PROD_HOSTNAME is separate — production targets are VPSes, not local VMs.
VM_CONFIGS = {
    "dev": {
        "name": os.environ.get("VM_HOSTNAME", "esacp-dev"),
        "inventory": "dev.yml",
        "snapshot": os.environ.get("SNAPSHOT_NAME", "baseline"),
        "description": "VirtualBox development VM"
    },
    "prod": {
        "name": os.environ.get("PROD_HOSTNAME", "esacp-prod"),
        "inventory": "prod.yml",
        "snapshot": None,  # Production VPSes don't use snapshots
        "description": "Production VPS deployment"
    }
}


def print_banner(message):
    """Print a formatted banner message"""
    console.print(Panel(f"[bold]{message}[/bold]", expand=False))


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    console.print(f"[dim]→ {' '.join(cmd)}[/dim]")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Command failed with exit code {e.returncode}[/red]")
        if capture_output:
            console.print(f"STDOUT: {e.stdout}")
            console.print(f"STDERR: {e.stderr}")
        sys.exit(1)


_VBOXMANAGE_WSL_PATH = "/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"


def find_vboxmanage():
    """Locate VBoxManage, handling native Linux and WSL on Windows."""
    for candidate in ("VBoxManage", "VBoxManage.exe"):
        if shutil.which(candidate):
            return candidate
    if Path(_VBOXMANAGE_WSL_PATH).exists():
        return _VBOXMANAGE_WSL_PATH
    return None


def check_prerequisites(need_vboxmanage=False):
    """Verify required tools are installed"""
    print_banner("Checking Prerequisites")

    required_tools = {
        "ansible": "ansible --version",
        "ansible-playbook": "ansible-playbook --version",
        "sops": "sops --version",
        "age": "age --version",
    }

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Tool", style="cyan", min_width=20)
    table.add_column("Status", min_width=12)

    missing = []
    for tool, check_cmd in required_tools.items():
        try:
            subprocess.run(
                check_cmd.split(),
                check=True,
                capture_output=True
            )
            table.add_row(tool, "[green]✓ Found[/green]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            table.add_row(tool, "[red]✗ Missing[/red]")
            missing.append(tool)

    if need_vboxmanage:
        vbm = find_vboxmanage()
        if vbm:
            table.add_row("VBoxManage", f"[green]✓ Found[/green] [dim]({vbm})[/dim]")
        else:
            table.add_row("VBoxManage", "[red]✗ Missing[/red]")
            missing.append("VBoxManage")

    console.print(table)

    if missing:
        console.print(f"\n[red]❌ Missing required tools: {', '.join(missing)}[/red]")
        console.print("Please install them before continuing.")
        sys.exit(1)

    console.print("\n[green]✅ All prerequisites satisfied[/green]")


def revert_vm_to_baseline(vm_name, snapshot_name):
    """Revert VM to baseline snapshot"""
    print_banner(f"Reverting {vm_name} to snapshot: {snapshot_name}")

    revert_script = ORCHESTRATION_DIR / "revertToBaseline.py"
    if not revert_script.exists():
        console.print(f"[yellow]⚠️  revertToBaseline.py not found at {revert_script}[/yellow]")
        console.print("    Skipping snapshot revert")
        return False

    run_command([
        "python3",
        str(revert_script),
        "--vm", vm_name,
        "--snapshot", snapshot_name
    ])

    console.print(f"[green]✅ VM reverted to {snapshot_name}[/green]")
    return True


def wait_for_ssh(inventory_file, timeout=300):
    """Wait for SSH to become available"""
    print_banner("Waiting for SSH Connection")

    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Waiting for SSH... ({task.fields[elapsed]}s elapsed)[/cyan]"),
        transient=True,
    ) as progress:
        task = progress.add_task("waiting", elapsed=0)

        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    [
                        "ansible",
                        "all",
                        "-i", str(ANSIBLE_DIR / "inventory" / inventory_file),
                        "-m", "ping",
                        "--one-line"
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )

                if "SUCCESS" in result.stdout:
                    console.print("[green]✅ SSH connection established[/green]")
                    return True
            except subprocess.CalledProcessError:
                pass

            elapsed = int(time.time() - start_time)
            progress.update(task, elapsed=elapsed)
            time.sleep(5)

    console.print(f"[red]❌ SSH connection timeout after {timeout} seconds[/red]")
    return False


def run_ansible_playbook(inventory_file, check_mode=False, tags=None):
    """Execute Ansible playbook"""
    print_banner("Running Ansible Playbook")

    # Ensure ansible.cfg is loaded from ansible/ regardless of CWD
    env = os.environ.copy()
    env["ANSIBLE_CONFIG"] = str(ANSIBLE_DIR / "ansible.cfg")

    # SSH key: honour SSH_KEY_PATH env var, fall back to default
    ssh_key_path = os.environ.get("SSH_KEY_PATH", os.path.expanduser("~/.ssh/id_ed25519"))
    env["ANSIBLE_PRIVATE_KEY_FILE"] = ssh_key_path

    # Remote user: honour ADMIN_USER_NAME env var if set (inventory takes precedence
    # at the host level, but this provides a controller-wide fallback)
    admin_user = os.environ.get("ADMIN_USER_NAME")
    if admin_user:
        env["ANSIBLE_REMOTE_USER"] = admin_user

    cmd = [
        "ansible-playbook",
        "-i", str(ANSIBLE_DIR / "inventory" / inventory_file),
        str(ANSIBLE_DIR / "site.yml"),
        "-v"
    ]

    if check_mode:
        cmd.append("--check")
        console.print("[cyan]ℹ️  Running in CHECK mode (dry run)[/cyan]")

    if tags:
        cmd.extend(["--tags", tags])
        console.print(f"[cyan]ℹ️  Running only tags: {tags}[/cyan]")

    console.print(f"[dim]→ {' '.join(cmd)}[/dim]")
    try:
        subprocess.run(cmd, check=True, env=env, text=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ ansible-playbook failed with exit code {e.returncode}[/red]")
        sys.exit(1)

    console.print("\n[green]✅ Ansible playbook completed successfully[/green]")


def main():
    parser = argparse.ArgumentParser(
        description="ESACP Provisioning Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--target",
        choices=["dev", "prod"],
        required=True,
        help="Target environment to provision"
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="Revert VM to baseline snapshot before provisioning"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run in check mode (dry run, no changes)"
    )
    parser.add_argument(
        "--tags",
        help="Only run specific Ansible tags (comma-separated)"
    )
    parser.add_argument(
        "--skip-ssh-wait",
        action="store_true",
        help="Skip waiting for SSH (use if VM is already running)"
    )

    args = parser.parse_args()
    config = VM_CONFIGS[args.target]

    print_banner(f"ESACP Provisioner — {config['description']}")

    info = Table(show_header=False, box=None, padding=(0, 2))
    info.add_column("Key", style="cyan")
    info.add_column("Value")
    info.add_row("Target", args.target)
    info.add_row("VM", config["name"])
    info.add_row("Inventory", config["inventory"])
    if args.revert:
        info.add_row("Snapshot", str(config["snapshot"]))
    console.print(info)

    # Step 1: Check prerequisites
    check_prerequisites(need_vboxmanage=args.revert and args.target == "dev")

    # Step 2: Revert VM to baseline (if requested and supported)
    if args.revert:
        if config["snapshot"]:
            revert_vm_to_baseline(config["name"], config["snapshot"])
        else:
            console.print(f"[yellow]⚠️  Snapshot revert not supported for {args.target}[/yellow]")

    # Step 3: Wait for SSH (if not skipped)
    if not args.skip_ssh_wait:
        if not wait_for_ssh(config["inventory"]):
            console.print("[red]❌ Cannot proceed without SSH access[/red]")
            sys.exit(1)

    # Step 4: Run Ansible playbook
    run_ansible_playbook(
        config["inventory"],
        check_mode=args.check,
        tags=args.tags
    )

    # Done
    print_banner("✅ Provisioning Complete!")

    vm_ip = os.environ.get("VM_IP", "<VM_IP>")
    services = Table(title="Access Services", show_header=True, header_style="bold cyan")
    services.add_column("Service", style="cyan")
    services.add_column("URL")
    services.add_row("Grafana", f"http://{vm_ip}:3000")
    services.add_row("Prometheus", f"http://{vm_ip}:9090")
    services.add_row("Alertmanager", f"http://{vm_ip}:9093")
    console.print(services)

    return 0


if __name__ == "__main__":
    sys.exit(main())
