"""Inspect and tear down a VM on the local libvirt daemon.

Used by the legacy ``esacp.py destroyVM`` subcommand (local-only). All subprocess
calls stay inside this primitive so the CLI dispatcher remains subprocess-free.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


IMAGES_DIR = Path("/var/lib/libvirt/images")


@dataclass(frozen=True)
class LocalVmInfo:
    exists: bool
    state: str
    snapshots: list[str]
    disk: Path | None
    seed: Path | None


def inspect_local_vm(vm: str) -> LocalVmInfo:
    """Probe local libvirt for *vm* and return a summary."""
    dominfo = subprocess.run(["virsh", "dominfo", vm], capture_output=True)
    if dominfo.returncode != 0:
        return LocalVmInfo(exists=False, state="", snapshots=[], disk=None, seed=None)

    state_r = subprocess.run(
        ["virsh", "domstate", vm], capture_output=True, text=True,
    )
    state = state_r.stdout.strip()

    snap_r = subprocess.run(
        ["virsh", "snapshot-list", vm, "--name"], capture_output=True, text=True,
    )
    snapshots = [s for s in snap_r.stdout.strip().splitlines() if s]

    disk = IMAGES_DIR / f"{vm}.qcow2"
    seed = IMAGES_DIR / f"{vm}-seed.iso"
    return LocalVmInfo(
        exists=True, state=state, snapshots=snapshots,
        disk=disk if disk.exists() else None,
        seed=seed if seed.exists() else None,
    )


def destroy_local_vm(vm: str, state: str, emit: Emit) -> None:
    """virsh destroy (if running) + undefine with storage + remove seed ISO.

    Raises RuntimeError if ``virsh undefine`` fails.
    """
    if state == "running":
        emit(f"  Forcing off {vm}…")
        subprocess.run(["virsh", "destroy", vm], capture_output=True)

    emit(f"  Undefining {vm} (--snapshots-metadata --remove-all-storage)…")
    r = subprocess.run(
        ["virsh", "undefine", vm, "--snapshots-metadata", "--remove-all-storage"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"virsh undefine failed: {r.stderr.strip()}")

    seed = IMAGES_DIR / f"{vm}-seed.iso"
    if seed.exists():
        emit(f"  Removing seed ISO: {seed}")
        subprocess.run(["sudo", "rm", "-f", str(seed)])
