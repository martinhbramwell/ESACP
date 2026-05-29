"""CLI: create or list KVM VM snapshots via the snapshot_ops primitive (#206)."""

from __future__ import annotations

from tools.cli._common import banner, kvm_hosts
from tools.pipeline.orchestration import snapshot_ops


def run(args, config: dict) -> int:
    vm = args.vm
    name = args.name
    hypervisor = kvm_hosts(config).get(vm, {}).get("hypervisor") or None

    if name:
        banner(f"Snapshot: {vm} / {name}")
        if name in snapshot_ops.list_snapshots(vm, hypervisor=hypervisor):
            print(f"  Snapshot '{name}' already exists on {vm} — skipping.")
            return 0
        return 0 if snapshot_ops.create_snapshot(vm, name, emit=print, hypervisor=hypervisor) else 1

    banner(f"Snapshots: {vm}")
    snapshots = snapshot_ops.list_snapshots(vm, hypervisor=hypervisor)
    if not snapshots:
        print(f"  (no snapshots on {vm})")
        return 0
    for s in snapshots:
        print(f"  {s}")
    return 0
