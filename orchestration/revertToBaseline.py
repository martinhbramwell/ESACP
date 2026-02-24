#!/usr/bin/env python3
"""
ESACP VM Snapshot Reverter
Reverts a VirtualBox VM to a named snapshot

Usage:
    python3 revertToBaseline.py --vm esacp-dev --snapshot baseline
"""

import argparse
import subprocess
import sys
import time


def run_vboxmanage(args, check=True):
    """Run VBoxManage command"""
    cmd = ["VBoxManage"] + args
    print(f"→ {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ VBoxManage failed: {e.stderr}")
        if check:
            sys.exit(1)
        return None


def get_vm_state(vm_name):
    """Get current state of VM"""
    result = run_vboxmanage(["showvminfo", vm_name, "--machinereadable"])
    
    for line in result.stdout.splitlines():
        if line.startswith("VMState="):
            state = line.split("=")[1].strip('"')
            return state
    
    return "unknown"


def power_off_vm(vm_name):
    """Power off VM if it's running"""
    state = get_vm_state(vm_name)
    print(f"VM {vm_name} state: {state}")
    
    if state == "running":
        print(f"⏸️  Powering off {vm_name}...")
        run_vboxmanage(["controlvm", vm_name, "poweroff"])
        
        # Wait for shutdown
        for i in range(30):
            time.sleep(1)
            state = get_vm_state(vm_name)
            if state == "poweroff":
                print(f"✅ VM powered off")
                return True
            print(".", end="", flush=True)
        
        print(f"\n⚠️  VM may not have shut down cleanly")
        return False
    
    elif state in ["poweroff", "saved"]:
        print(f"✅ VM already powered off")
        return True
    
    else:
        print(f"⚠️  Unexpected VM state: {state}")
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
    print(f"🔄 Restoring {vm_name} to snapshot: {snapshot_name}")
    
    run_vboxmanage([
        "snapshot", vm_name, "restore", snapshot_name
    ])
    
    print(f"✅ Snapshot restored")


def start_vm(vm_name, headless=True):
    """Start VM"""
    print(f"▶️  Starting {vm_name}...")
    
    vm_type = "headless" if headless else "gui"
    run_vboxmanage(["startvm", vm_name, "--type", vm_type])
    
    print(f"✅ VM started in {vm_type} mode")
    
    # Give it a few seconds to boot
    print("⏳ Waiting for boot...")
    time.sleep(10)


def main():
    parser = argparse.ArgumentParser(
        description="Revert VirtualBox VM to baseline snapshot"
    )
    
    parser.add_argument(
        "--vm",
        required=True,
        help="Name of the VirtualBox VM"
    )
    
    parser.add_argument(
        "--snapshot",
        required=True,
        help="Name of the snapshot to restore"
    )
    
    parser.add_argument(
        "--no-start",
        action="store_true",
        help="Don't start the VM after restoring"
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Start VM in GUI mode instead of headless"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"  ESACP VM Snapshot Reverter")
    print("=" * 60)
    print(f"VM: {args.vm}")
    print(f"Snapshot: {args.snapshot}")
    print()
    
    # Check if VM exists
    result = run_vboxmanage(["list", "vms"], check=False)
    if not result or args.vm not in result.stdout:
        print(f"❌ VM '{args.vm}' not found")
        print("\nAvailable VMs:")
        if result:
            print(result.stdout)
        sys.exit(1)
    
    # Check if snapshot exists
    if not snapshot_exists(args.vm, args.snapshot):
        print(f"❌ Snapshot '{args.snapshot}' not found for VM '{args.vm}'")
        print("\nAvailable snapshots:")
        run_vboxmanage(["snapshot", args.vm, "list"], check=False)
        sys.exit(1)
    
    # Power off VM
    if not power_off_vm(args.vm):
        response = input("\n⚠️  Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Restore snapshot
    restore_snapshot(args.vm, args.snapshot)
    
    # Start VM
    if not args.no_start:
        start_vm(args.vm, headless=not args.gui)
    
    print("\n" + "=" * 60)
    print("  ✅ VM Restoration Complete")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
