"""Snapshot operations — list and create libvirt snapshots (local or remote)."""

from __future__ import annotations

import subprocess
import time

from tools.pipeline.stages.common.types import Emit

# The post-provision snapshot can fail transiently right after heavy bench/site
# disk I/O ("Extra element disks in interleave" on toshiba's libvirt 6.0.0); it
# self-resolves within seconds. Retry a few times before giving up (ESACP #658).
_SNAPSHOT_RETRIES = 3
_SNAPSHOT_BACKOFF_S = 3.0


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
    *, retries: int = _SNAPSHOT_RETRIES, backoff_s: float = _SNAPSHOT_BACKOFF_S,
) -> bool:
    """Take an atomic snapshot, retrying transient failures.

    Emits a status line. Returns True on success, False once *retries*
    attempts are exhausted. Callers MUST act on a False return — a missing
    snapshot breaks the idempotency gate, rollback, and self-repair (#658).
    """
    last_err = ""
    for attempt in range(1, retries + 1):
        r = subprocess.run(
            _virsh_cmd("snapshot-create-as", vm, name, "--atomic", hypervisor=hypervisor),
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0:
            emit(f"  [OK] Snapshot '{name}' taken")
            return True
        last_err = r.stderr.strip()
        if attempt < retries:
            emit(f"  [WARN] Snapshot '{name}' attempt {attempt}/{retries} failed: "
                 f"{last_err} — retrying in {backoff_s:g}s")
            time.sleep(backoff_s)
    emit(f"  [WARN] Snapshot '{name}' failed after {retries} attempts: {last_err}")
    return False


def snapshot_or_raise(
    vm: str, name: str, emit: Emit, hypervisor: str | None = None,
) -> None:
    """Take a snapshot; a failure is a hard error (raises RuntimeError).

    A missing post-provision snapshot leaves a VM with no Baseline, silently
    breaking the idempotency gate, rollback, and self-repair — so provision
    macros use this, not the bool-returning create_snapshot (ESACP #658).
    """
    if not create_snapshot(vm, name, emit, hypervisor):
        raise RuntimeError(
            f"Provision failed: snapshot '{name}' could not be created after "
            f"retries — VM has no Baseline (idempotency/rollback broken)."
        )
