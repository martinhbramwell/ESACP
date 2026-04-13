"""Destroy a VM on its hypervisor: delete snapshots, stop, undefine + remove storage."""

from __future__ import annotations

import subprocess

from tools.pipeline.stages.common.types import Emit


def destroy_vm(hostname: str, hypervisor: str, emit: Emit) -> None:
    """Fully destroy *hostname* on *hypervisor*.

    Deletes all snapshots (handles hierarchical trees), then
    ``virsh destroy`` + ``virsh undefine --remove-all-storage``.
    Tolerates already-stopped or already-absent domains.
    """
    if not hypervisor:
        raise RuntimeError(f"No hypervisor specified for '{hostname}'")

    # Delete all snapshots first — libvirt refuses to undefine a domain
    # that has snapshots.
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
                emit(f"  [OK] {virsh_cmd} — already stopped or absent")
            else:
                raise RuntimeError(f"'{virsh_cmd}' failed: {r.stderr.strip()}")
        else:
            emit(f"  [OK] {virsh_cmd}")
