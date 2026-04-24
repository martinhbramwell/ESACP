"""Bench-layer gate applied before golden-backup capture.

Refuses to stage a .tgz whose source VM does not satisfy Stage 6
generic-mode postconditions. Guards against the regression class
that produced the contaminated B03/B06/B07 fixtures before #289:
wizard + site layer could appear clean while the bench layer
carried ce_sri / route_planner / returnable + patched Procfile
and /opt/ce_sri/envars.sh. See #292.
"""

from __future__ import annotations

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.stage_6_base_platform.verify import (
    all_passed,
    verify_stage_6,
)


def assert_clean_bench(config, emit: Emit) -> None:
    """Raise RuntimeError if the VM's bench is not generic-clean."""
    results = verify_stage_6(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
        erp_user=config.erp_user,
        bench_dir=config.bench_dir,
        provision_mode="generic",
    )
    if not all_passed(results):
        failures = [msg for ok, msg in results if not ok]
        raise RuntimeError(
            "Bench-layer gate failed — refusing to stage contaminated "
            "fixture (#289, #292):\n"
            + "\n".join(f"  [FAIL] {m}" for m in failures)
        )
    for _, msg in results:
        emit(f"  [OK] {msg}")
