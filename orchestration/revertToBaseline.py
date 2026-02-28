#!/usr/bin/env python3
"""
ESACP VM Snapshot Reverter
Reverts a VirtualBox VM to a named snapshot

Usage:
    python3 revertToBaseline.py --vm esacp-dev --snapshot "Ready for Provisioning"
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()

# Well-known VirtualBox installation path on Windows (accessed from WSL)
_VBOXMANAGE_WSL_PATH = "/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"


def find_vboxmanage():
    """
    Locate VBoxManage, handling native Linux and WSL on Windows.
    Returns the binary path string, or None if not found.
    """
    for candidate in ("VBoxManage", "VBoxManage.exe"):
        if shutil.which(candidate):
            return candidate
    if Path(_VBOXMANAGE_WSL_PATH).exists():
        return _VBOXMANAGE_WSL_PATH
    return None


# Resolved once at module load; revertToBaseline cannot run without it.
_VBOXMANAGE = find_vboxmanage()
if _VBOXMANAGE is None:
    console.print(
        "[red]❌ VBoxManage not found.[/red]\n"
        "Add the VirtualBox installation directory to PATH, or ensure\n"
        f"VBoxManage.exe exists at: {_VBOXMANAGE_WSL_PATH}"
    )
    sys.exit(1)


def run_vboxmanage(args, check=True):
    """Run VBoxManage command"""
    cmd = [_VBOXMANAGE] + args
    console.print(f"[dim]→ {' '.join(cmd)}[/dim]")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ VBoxManage failed: {e.stderr.strip()}[/red]")
        if check:
            sys.exit(1)
        return None


def get_vm_state(vm_name):
    """Get current state of VM"""
    result = run_vboxmanage(["showvminfo", vm_name, "--machinereadable"])

    for line in result.stdout.splitlines():
        if line.startswith("VMState="):
            return line.split("=")[1].strip('"')

    return "unknown"


def power_off_vm(vm_name):
    """Power off VM if it's running"""
    state = get_vm_state(vm_name)
    console.print(f"VM [cyan]{vm_name}[/cyan] state: [yellow]{state}[/yellow]")

    if state == "running":
        console.print(f"[yellow]⏸️  Powering off {vm_name}...[/yellow]")
        run_vboxmanage(["controlvm", vm_name, "poweroff"])

        for _ in range(30):
            time.sleep(1)
            state = get_vm_state(vm_name)
            if state == "poweroff":
                console.print("[green]✅ VM powered off[/green]")
                return True
            console.print(".", end="", highlight=False)

        console.print(f"\n[yellow]⚠️  VM may not have shut down cleanly[/yellow]")
        return False

    elif state in ["poweroff", "saved"]:
        console.print("[green]✅ VM already powered off[/green]")
        return True

    else:
        console.print(f"[yellow]⚠️  Unexpected VM state: {state}[/yellow]")
        return False


def snapshot_exists(vm_name, snapshot_name):
    """Check if snapshot exists"""
    result = run_vboxmanage(
        ["snapshot", vm_name, "list", "--machinereadable"],
        check=False
    )

    if result and result.returncode == 0:
        for line in result.stdout.splitlines():
            if f'SnapshotName="{snapshot_name}"' in line:
                return True

    return False


def restore_snapshot(vm_name, snapshot_name):
    """Restore VM to snapshot"""
    console.print(
        f"[cyan]🔄 Restoring [bold]{vm_name}[/bold] "
        f"to snapshot: [bold]{snapshot_name}[/bold][/cyan]"
    )
    run_vboxmanage(["snapshot", vm_name, "restore", snapshot_name])
    console.print("[green]✅ Snapshot restored[/green]")
    # VirtualBox holds a session lock briefly after snapshot restore;
    # wait for it to release before attempting startvm.
    console.print("[dim]⏳ Waiting for session lock to release...[/dim]")
    time.sleep(5)


def start_vm(vm_name, headless=True):
    """Start VM"""
    vm_type = "headless" if headless else "gui"
    console.print(f"[cyan]▶️  Starting {vm_name} ({vm_type})...[/cyan]")
    run_vboxmanage(["startvm", vm_name, "--type", vm_type])
    console.print(f"[green]✅ VM started in {vm_type} mode[/green]")
    console.print("[dim]⏳ Waiting for boot...[/dim]")
    time.sleep(10)


def main():
    parser = argparse.ArgumentParser(
        description="Revert VirtualBox VM to baseline snapshot"
    )

    parser.add_argument("--vm", required=True, help="Name of the VirtualBox VM")
    parser.add_argument("--snapshot", required=True, help="Name of the snapshot to restore")
    parser.add_argument("--no-start", action="store_true",
                        help="Don't start the VM after restoring")
    parser.add_argument("--gui", action="store_true",
                        help="Start VM in GUI mode instead of headless")

    args = parser.parse_args()

    console.print(Panel(
        f"[bold]ESACP VM Snapshot Reverter[/bold]\n"
        f"VM: [cyan]{args.vm}[/cyan]  •  Snapshot: [cyan]{args.snapshot}[/cyan]",
        expand=False
    ))

    # Check if VM exists
    result = run_vboxmanage(["list", "vms"], check=False)
    if not result or args.vm not in result.stdout:
        console.print(f"[red]❌ VM '{args.vm}' not found[/red]")
        console.print("\nAvailable VMs:")
        if result:
            console.print(result.stdout)
        sys.exit(1)

    # Check if snapshot exists
    if not snapshot_exists(args.vm, args.snapshot):
        console.print(f"[red]❌ Snapshot '{args.snapshot}' not found for VM '{args.vm}'[/red]")
        console.print("\nAvailable snapshots:")
        run_vboxmanage(["snapshot", args.vm, "list"], check=False)
        sys.exit(1)

    # Power off VM
    if not power_off_vm(args.vm):
        response = input("\n⚠️  Continue anyway? (y/N): ")
        if response.lower() != "y":
            sys.exit(1)

    # Restore snapshot
    restore_snapshot(args.vm, args.snapshot)

    # Start VM
    if not args.no_start:
        start_vm(args.vm, headless=not args.gui)

    console.print(Panel("[bold green]✅ VM Restoration Complete[/bold green]", expand=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
