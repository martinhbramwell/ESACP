"""Snapshot operations — list and create libvirt snapshots (local or remote)."""

from __future__ import annotations

import subprocess

from tools.pipeline.stages.common.types import Emit


def _virsh_cmd(action: str, *args: str, hypervisor: str | None = None) -> list[str]:
    if hypervisor:
        return ["ssh", hypervisor, "virsh", "--connect", "qemu:///system", action, *args]
    return ["virsh", action, *args]


def list_snapshots(vm: str, hypervisor: str | None = None) -> list[str]:
    """Return snapshot names for *vm* (empty list on error)."""
    r = subprocess.run(
        _virsh_cmd("snapshot-list", vm, "--name", hypervisor=hypervisor),
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        return []
    return [s for s in r.stdout.strip().splitlines() if s]


def create_snapshot(
    vm: str, name: str, emit: Emit, hypervisor: str | None = None,
) -> bool:
    """Take an atomic snapshot. Emits a status line. Returns True on success."""
    r = subprocess.run(
        _virsh_cmd("snapshot-create-as", vm, name, "--atomic", hypervisor=hypervisor),
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode == 0:
        emit(f"  [OK] Snapshot '{name}' taken")
        return True
    emit(f"  [WARN] Snapshot '{name}' failed: {r.stderr.strip()}")
    return False


def revert_snapshot(
    vm: str, name: str, emit: Emit, hypervisor: str | None = None,
) -> bool:
    """Revert *vm* to snapshot *name*, leaving it running. Returns True on success."""
    r = subprocess.run(
        _virsh_cmd("snapshot-revert", vm, name, "--running", hypervisor=hypervisor),
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode == 0:
        emit(f"  [OK] Reverted to snapshot '{name}'")
        return True
    emit(f"  [WARN] Revert to '{name}' failed: {r.stderr.strip()}")
    return False
