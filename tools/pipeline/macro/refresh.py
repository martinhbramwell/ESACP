"""Macro: refresh an existing ERPNext VM (stages 3–9)."""

from __future__ import annotations

from tools.pipeline.stages.common.config import build_config
from tools.pipeline.stages.common.log_format import stage_banner
from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.stage_3_connectivity import run_stage_3
from tools.pipeline.stages.stage_4_content_delivery import run_stage_4
from tools.pipeline.stages.stage_5_tls import run_stage_5
from tools.pipeline.stages.stage_6_base_platform import run_stage_6
from tools.pipeline.stages.stage_7_data_restoration import run_stage_7
from tools.pipeline.stages.stage_8_app_config import run_stage_8
from tools.pipeline.stages.stage_9_service_activation import run_stage_9


def run(
    hostname: str,
    host_cfg: dict,
    project_root: str,
    emit: Emit,
    *,
    force: bool = False,
) -> None:
    """Refresh an existing ERPNext VM by running stages 3–9.

    Uses WireGuard transport (VM already exists, WG is up).
    Raises RuntimeError on the first stage that fails.

    When ``force=True`` (#492), stages 4 (content delivery) and 5 (TLS)
    bypass their presence-based verify-skip gates so template-only edits
    are redeployed. Other stages keep their normal idempotency — in
    particular stage 7 (data restoration) is never force-rerun.
    """
    config = build_config(hostname, host_cfg, project_root,
                          use_wg=True, force_refresh=force)
    if force:
        emit("[WARN] force_refresh=True — stages 4+5 will bypass verify-skip gates")

    _STAGES: list[tuple[str, object]] = [
        ("Stage 3: Connectivity",       run_stage_3),
        ("Stage 4: Content Delivery",   run_stage_4),
        ("Stage 5: TLS",                run_stage_5),
        ("Stage 6: Base Platform",      run_stage_6),
        ("Stage 7: Data Restoration",   run_stage_7),
        ("Stage 8: App Config",         run_stage_8),
        ("Stage 9: Service Activation", run_stage_9),
    ]
    for label, stage_fn in _STAGES:
        emit(stage_banner(label))
        stage_fn(config, emit)
