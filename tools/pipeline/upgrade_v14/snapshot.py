"""Stage 2 — virsh snapshot on hypervisor before destructive V14 upgrade."""

from __future__ import annotations

import time

from tools.pipeline.orchestration.virsh import virsh_ssh
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

SNAPSHOT_PREFIX = "pre-V14-upgrade"


def take_snapshot(config: Config, emit: Emit) -> TaskResult:
    if not config.hypervisor:
        return TaskResult(False, False, "No hypervisor in config — cannot snapshot")
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = f"{SNAPSHOT_PREFIX}-{config.hostname}-{ts}"
    emit(f"  Taking snapshot {name} on {config.hypervisor}")
    # #688: virsh runs without sudo (operator is in the libvirt group); `sudo
    # virsh` over non-interactive SSH fails for want of a TTY. Route through the
    # shared virsh_ssh helper, consistent with vm_power.py.
    r = virsh_ssh(
        config.hypervisor,
        f"snapshot-create-as --domain {config.hostname} --name {name} "
        f"--description 'Phase 5 V14 upgrade rollback point'",
        timeout=300,
    )
    if r.returncode != 0:
        return TaskResult(False, False, f"snapshot-create-as failed: {r.stderr.strip()}")
    emit(f"  ✓ Snapshot {name} created")
    return TaskResult(True, True, f"Snapshot {name} created")
