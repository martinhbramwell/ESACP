"""Unit: take Baseline snapshot after successful boot (Step 7)."""

from __future__ import annotations

import subprocess

from tools.pipeline.stages.common.types import Emit


def take_baseline_snapshot(
    hostname: str, hypervisor_alias: str, emit: Emit,
) -> None:
    """Create a 'Baseline' snapshot on the hypervisor."""
    r = subprocess.run(
        ["ssh", hypervisor_alias,
         f"virsh --connect qemu:///system snapshot-create-as {hostname} 'Baseline' --atomic"],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        emit(f"  [WARN] Baseline snapshot failed: {r.stderr.strip()}")
    else:
        emit("  [OK] Baseline snapshot taken")
