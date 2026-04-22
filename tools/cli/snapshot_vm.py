"""CLI: create or list KVM VM snapshots via the snapshot_ops primitive (#206)."""

from __future__ import annotations

from tools.cli._common import banner
from tools.pipeline.orchestration import snapshot_ops


def run(args, config: dict) -> int:
    vm = args.vm
    name = args.name

    if name:
        banner(f"Snapshot: {vm} / {name}")
        if name in snapshot_ops.list_snapshots(vm):
            print(f"  Snapshot '{name}' already exists on {vm} — skipping.")
            return 0
        return 0 if snapshot_ops.create_snapshot(vm, name, emit=print) else 1

    banner(f"Snapshots: {vm}")
    snapshots = snapshot_ops.list_snapshots(vm)
    if not snapshots:
        print(f"  (no snapshots on {vm})")
        return 0
    for s in snapshots:
        print(f"  {s}")
    return 0
