"""Stage 3: Connectivity — deploy keys, controller pubkey, ce_sri secrets, backup, DDL.

Orchestrates Steps 10–11 of the provision pipeline.  Extracted from
``_run_provision_erpnext`` in api.py.
"""

from __future__ import annotations

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.types import Config, Emit

from .backup import ensure_backup
from .cesri_secrets import ensure_cesri_secrets
from .controller_pubkey import ensure_controller_pubkey
from .ddl_views import ensure_ddl_views
from .deploy_keys import ensure_deploy_keys
from .verify import all_passed, verify_stage_3


def run_stage_3(config: Config, emit: Emit) -> None:
    """Execute connectivity setup (Steps 10–11).

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
    results = verify_stage_3(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
        erp_user=config.erp_user,
        bench_dir_orig=config.bench_dir_orig,
    )
    if all_passed(results):
        emit("[OK] Stage 3 already satisfied — skipping")
        return

    # ── Deploy keys ──
    emit(step_header("SCP deploy keys"))
    r = ensure_deploy_keys(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    # ── Controller pubkey ──
    emit(step_header("SCP controller pubkey"))
    r = ensure_controller_pubkey(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    if config.provision_mode == "generic":
        emit("  [SKIP] ce_sri secrets — generic mode")
        emit("  [SKIP] database backup — generic mode")
        emit("  [SKIP] ddlViews.sql — generic mode")
        return

    # ── ce_sri secrets ──
    emit(step_header("ce_sri secrets (SOPS decrypt + patch + SCP)"))
    r = ensure_cesri_secrets(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    # ── Rsync database backup ──
    emit(step_header("Rsync database backup"))
    r = ensure_backup(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    # ── ddlViews.sql ──
    emit(step_header("SCP ddlViews.sql"))
    r = ensure_ddl_views(config, emit)
    if not r.success:
        emit(f"  [WARN] {r.message}")
    else:
        tag = "[CHANGED]" if r.changed else "[OK]"
        emit(f"  {tag} {r.message}")
