"""Unit: clean up residue from a previous build (Step 0).

If the VM hostname exists on the hypervisor but is not fully provisioned
(no Baseline snapshot), destroy leftover VM + storage so vol-clone
doesn't collide.
"""

from __future__ import annotations

import subprocess

from tools.pipeline.stages.common.types import Emit


def cleanup_residue(
    hostname: str, host_cfg: dict, hypervisor: str, emit: Emit,
) -> None:
    """Destroy a leftover VM (snapshots, domain, storage) on *hypervisor*."""
    if not hypervisor:
        raise RuntimeError(f"No hypervisor configured for '{hostname}'")

    # Delete all snapshots first — libvirt refuses to undefine a domain
    # that has snapshots.  Loop handles hierarchical trees.
    for _attempt in range(20):
        snap_r = subprocess.run(
            ["ssh", hypervisor,
             f"virsh --connect qemu:///system snapshot-list {hostname} --name"],
            capture_output=True, text=True, timeout=30,
        )
        snapshots = [s.strip() for s in snap_r.stdout.strip().splitlines() if s.strip()]
        if not snapshots:
            break
        for snap_name in snapshots:
            del_r = subprocess.run(
                ["ssh", hypervisor,
                 f"virsh --connect qemu:///system snapshot-delete {hostname} '{snap_name}'"],
                capture_output=True, text=True, timeout=60,
            )
            if del_r.returncode == 0:
                emit(f"  [OK] Deleted snapshot: {snap_name}")
            else:
                emit(f"  [WARN] snapshot-delete {snap_name}: {del_r.stderr.strip()}")

    for virsh_cmd in (
        f"virsh --connect qemu:///system destroy {hostname}",
        f"virsh --connect qemu:///system undefine {hostname} --remove-all-storage",
    ):
        r = subprocess.run(
            ["ssh", hypervisor, virsh_cmd],
            capture_output=True, text=True, timeout=60,
        )
        combined = (r.stdout + r.stderr).lower()
        if r.returncode != 0:
            if "domain is not running" in combined or "failed to get domain" in combined:
                emit(f"  [OK] {virsh_cmd} — VM was already stopped or absent")
            else:
                raise RuntimeError(f"'{virsh_cmd}' failed: {r.stderr.strip()}")
        else:
            emit(f"  [OK] {virsh_cmd}")
