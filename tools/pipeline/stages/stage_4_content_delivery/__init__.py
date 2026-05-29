"""Stage 4: Content Delivery — render config artifacts + deploy bundle to VM.

Orchestrates Step 12 of the provision pipeline.  Extracted from
``_run_provision_erpnext`` in api.py.
"""

from __future__ import annotations

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.types import Config, Emit

from .config_bundle import render_and_deploy_config
from .verify import all_passed, verify_stage_4


def run_stage_4(config: Config, emit: Emit) -> None:
    """Execute content delivery (Step 12).

    Parameters
    ----------
    config : Config
        Immutable per-VM configuration.
    emit : Emit
        Log callback.

    Raises
    ------
    RuntimeError
        If any critical step fails.
    """
    # ── Idempotency gate: skip if all postconditions already met ──
    results = verify_stage_4(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
    )
    if all_passed(results) and not config.force_refresh:
        emit("[OK] Stage 4 already satisfied — skipping")
        return

    # ── Render config artifacts + deploy bundle ──
    emit(step_header("Render config + deploy bundle"))
    r = render_and_deploy_config(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")
