#!/usr/bin/env python3
"""
snapshot.py — KVM/virsh snapshot lifecycle manager for ESACP

Wraps virsh snapshot operations with consistent error handling and
human-friendly output. Used directly and by provision_kvm.py.

Usage:
    python platforms/kvm/snapshot.py create  <vm> <snapshot-name>
    python platforms/kvm/snapshot.py revert  <vm> <snapshot-name>
    python platforms/kvm/snapshot.py list    <vm>
    python platforms/kvm/snapshot.py delete  <vm> <snapshot-name>
    python platforms/kvm/snapshot.py start   <vm>
    python platforms/kvm/snapshot.py state   <vm>
"""

import subprocess
import sys
import argparse


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def state(vm: str) -> str:
    """Return the current domain state string (e.g. 'running', 'shut off')."""
    result = run(["virsh", "domstate", vm])
    return result.stdout.strip()


def start(vm: str) -> None:
    s = state(vm)
    if s == "running":
        print(f"  {vm} is already running.")
        return
    print(f"  Starting {vm}...")
    run(["virsh", "start", vm])
    print(f"  ✅  {vm} started.")


def snapshot_exists(vm: str, name: str) -> bool:
    result = run(["virsh", "snapshot-list", vm, "--name"], check=False)
    return name in result.stdout.splitlines()


def create(vm: str, name: str) -> None:
    if snapshot_exists(vm, name):
        print(f"  Snapshot '{name}' already exists on {vm} — skipping.")
        return
    print(f"  Taking snapshot '{name}' on {vm}...")
    run(["virsh", "snapshot-create-as", vm, name, "--atomic"])
    print(f"  ✅  Snapshot '{name}' created.")


def revert(vm: str, name: str) -> None:
    if not snapshot_exists(vm, name):
        print(f"ERROR: Snapshot '{name}' not found on {vm}.", file=sys.stderr)
        print(f"       Available snapshots:", file=sys.stderr)
        result = run(["virsh", "snapshot-list", vm, "--name"], check=False)
        for line in result.stdout.strip().splitlines():
            print(f"         {line}", file=sys.stderr)
        sys.exit(1)
    # Power off if running
    if state(vm) == "running":
        print(f"  Powering off {vm}...")
        run(["virsh", "destroy", vm])
    print(f"  Reverting {vm} to '{name}'...")
    run(["virsh", "snapshot-revert", vm, name])
    print(f"  ✅  {vm} reverted to '{name}'.")
    print(f"  Starting {vm}...")
    run(["virsh", "start", vm])
    print(f"  ✅  {vm} started.")


def list_snapshots(vm: str) -> None:
    result = run(["virsh", "snapshot-list", vm])
    print(result.stdout)


def delete(vm: str, name: str) -> None:
    if not snapshot_exists(vm, name):
        print(f"  Snapshot '{name}' not found on {vm} — nothing to delete.")
        return
    print(f"  Deleting snapshot '{name}' from {vm}...")
    run(["virsh", "snapshot-delete", vm, name])
    print(f"  ✅  Snapshot '{name}' deleted.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="KVM snapshot manager for ESACP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "action",
        choices=["create", "revert", "list", "delete", "start", "state"],
    )
    parser.add_argument("vm", help="VM domain name (e.g. saconsole, target1)")
    parser.add_argument("snapshot_name", nargs="?", help="Snapshot name (not needed for list/start/state)")

    args = parser.parse_args()

    if args.action in ("create", "revert", "delete") and not args.snapshot_name:
        parser.error(f"'snapshot_name' is required for action '{args.action}'")

    try:
        if args.action == "create":
            create(args.vm, args.snapshot_name)
        elif args.action == "revert":
            revert(args.vm, args.snapshot_name)
        elif args.action == "list":
            list_snapshots(args.vm)
        elif args.action == "delete":
            delete(args.vm, args.snapshot_name)
        elif args.action == "start":
            start(args.vm)
        elif args.action == "state":
            print(state(args.vm))
    except subprocess.CalledProcessError as e:
        print(f"ERROR: virsh command failed:\n  {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
