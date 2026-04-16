"""VM power primitives — start/stop/reboot via virsh over SSH.

Each primitive returns a human-readable message on success and raises:
- ``ValueError`` for policy violations (e.g. stopping the hub).
- ``RuntimeError`` for virsh/SSH failures.
"""

from __future__ import annotations

from tools.pipeline.orchestration.virsh import virsh_ssh
from tools.pipeline.stages.common.types import Emit


def start(hypervisor: str, hostname: str, emit: Emit) -> str:
    emit(f"virsh start {hostname} on {hypervisor}")
    r = virsh_ssh(hypervisor, f"start {hostname}")
    if r.returncode == 0:
        return f"{hostname} started"
    if "already active" in (r.stdout + r.stderr).lower():
        return f"{hostname} is already running"
    detail = r.stderr.strip() or r.stdout.strip()
    raise RuntimeError(f"virsh start failed: {detail}")


def stop(hypervisor: str, hostname: str, emit: Emit, is_hub: bool = False) -> str:
    if is_hub:
        raise ValueError(
            f"Cannot stop hub node '{hostname}' — this would break the mesh",
        )
    emit(f"virsh shutdown {hostname} on {hypervisor}")
    r = virsh_ssh(hypervisor, f"shutdown {hostname}")
    if r.returncode == 0:
        return f"{hostname} shutting down"
    if "domain is not running" in (r.stdout + r.stderr).lower():
        return f"{hostname} is already stopped"
    detail = r.stderr.strip() or r.stdout.strip()
    raise RuntimeError(f"virsh shutdown failed: {detail}")


def reboot(hypervisor: str, hostname: str, emit: Emit) -> str:
    emit(f"virsh reboot {hostname} on {hypervisor}")
    r = virsh_ssh(hypervisor, f"reboot {hostname}")
    if r.returncode == 0:
        return f"{hostname} rebooting"
    detail = r.stderr.strip() or r.stdout.strip()
    raise RuntimeError(f"virsh reboot failed: {detail}")
