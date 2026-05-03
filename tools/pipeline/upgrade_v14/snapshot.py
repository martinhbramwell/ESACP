"""Stage 2 — virsh snapshot on hypervisor before destructive V14 upgrade."""

from __future__ import annotations

import subprocess
import time

from tools.pipeline.stages.common.types import Config, Emit, TaskResult

SNAPSHOT_PREFIX = "pre-V14-upgrade"


def take_snapshot(config: Config, emit: Emit) -> TaskResult:
    if not config.hypervisor:
        return TaskResult(False, False, "No hypervisor in config — cannot snapshot")
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = f"{SNAPSHOT_PREFIX}-{config.hostname}-{ts}"
    cmd = ["ssh", config.hypervisor,
           f"sudo virsh --connect qemu:///system snapshot-create-as "
           f"--domain {config.hostname} --name {name} "
           f"--description 'Phase 5 V14 upgrade rollback point'"]
    emit(f"  Taking snapshot {name} on {config.hypervisor}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return TaskResult(False, False, f"snapshot-create-as failed: {r.stderr.strip()}")
    emit(f"  ✓ Snapshot {name} created")
    return TaskResult(True, True, f"Snapshot {name} created")
