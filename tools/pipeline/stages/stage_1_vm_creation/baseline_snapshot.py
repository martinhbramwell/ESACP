"""Unit: take Baseline snapshot after successful boot (Step 7)."""

from __future__ import annotations

from tools.pipeline.orchestration.snapshot_ops import snapshot_or_raise
from tools.pipeline.stages.common.types import Emit


def take_baseline_snapshot(
    hostname: str, hypervisor_alias: str, emit: Emit,
) -> None:
    """Create the 'Baseline' snapshot — the stage-1 idempotency-gate key.

    Delegates to ``snapshot_or_raise`` (single source of truth, retry-backed):
    a failure raises RuntimeError, matching the stage-1 unit failure contract
    (``virt_install``/``clone_template``/``wait_ssh`` all raise). A missing
    Baseline would silently break the idempotency gate that
    ``verify.check_baseline_snapshot`` keys on, plus rollback and self-repair
    (ESACP #660 — was a copy-paste of the virsh logic that warned-and-returned).
    """
    snapshot_or_raise(hostname, "Baseline", emit, hypervisor=hypervisor_alias)
