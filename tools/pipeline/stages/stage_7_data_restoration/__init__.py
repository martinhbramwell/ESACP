"""Stage 7: Data Restoration — site creation, app install, DB restore, fixture cleanup.

One bash script SCP'd to the VM and run via SSH:
  data_restore.sh — sections D, D1, E, E1, F, G-pre, G, G1, G2
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_7

_DIR = Path(__file__).parent
_DATA_RESTORE = _DIR / "data_restore.sh"
_DATA_INIT = _DIR / "data_init.sh"


def run_stage_7(config: Config, emit: Emit) -> None:
    """Execute data restoration (sections D–G2).

    Raises
    ------
    RuntimeError
        If any critical step fails.
    """
    results = verify_stage_7(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
        erp_user=config.erp_user,
        bench_dir=config.bench_dir,
        site_url=config.site_url,
    )
    # Stage 7 deliberately ignores config.force_refresh — data restoration
    # is destructive (re-restores from production backup, wiping any post-
    # restore lab state). #492 scopes force to stages 4 + 5 only.
    if all_passed(results):
        emit("[OK] Stage 7 already satisfied — skipping")
        return

    if config.provision_mode == "generic":
        _run_data_init(config, emit)
    else:
        _run_data_restore(config, emit)


def _run_data_init(config: Config, emit: Emit) -> None:
    """Generic mode: create a blank ERPNext site (no DB restore)."""
    emit(step_header("Data init (generic — blank site)"))

    r = scp_to_vm(config, [str(_DATA_INIT)], "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP data_init.sh failed: {r.stderr.strip()}")

    emit("  Running data_init.sh ...")
    cmd = (
        f"sudo bash /tmp/data_init.sh"
        f" {config.bench_dir} {config.site_url} {config.erp_user}"
        f" {config.db_root_pwd} {config.erp_user_pwd}"
    )
    r = ssh_run(config, cmd, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(
            f"data_init.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")


def _run_data_restore(config: Config, emit: Emit) -> None:
    """Restored mode: full data restoration from production backup."""
    emit(step_header("Data restoration (sections D\u2013G2)"))

    r = scp_to_vm(config, [str(_DATA_RESTORE)], "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP stage 7 script failed: {r.stderr.strip()}")

    emit("  Running data_restore.sh ...")
    cmd = (
        f"sudo bash /tmp/data_restore.sh"
        f" {config.bench_dir} {config.site_url} {config.erp_user}"
        f" {config.db_root_pwd} {config.erp_user_pwd}"
    )
    r = ssh_run(config, cmd, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(
            f"data_restore.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")
