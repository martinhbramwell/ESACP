"""Stage 8: App Config — service restart, API keys, secrets, .env, install.py.

Two bash scripts SCP'd to the VM and run via SSH:
  pre_restart_config.sh  — sections H, H2a, H2, H2b, H4a, H3, H4b, H4c, H4d
  post_restart_config.sh — sections H4e, H4f, H4f-poll, H4g

Note: H4a-sl (Social Login restore) belongs in Stage 10 — it needs
HTTPS from Stage 9.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_8

_DIR = Path(__file__).parent
_PRE_RESTART = _DIR / "pre_restart_config.sh"
_POST_RESTART = _DIR / "post_restart_config.sh"
_POLL_GUNICORN = (
    Path(__file__).resolve().parents[3] / "vm_scripts" / "poll_gunicorn.py"
)

GUNICORN_PORT = 8000


def run_stage_8(config: Config, emit: Emit) -> None:
    """Execute app configuration (sections H–H4g).

    Raises
    ------
    RuntimeError
        If any critical step fails.
    """
    results = verify_stage_8(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
        erp_user=config.erp_user,
        bench_dir=config.bench_dir,
        site_url=config.site_url,
        gunicorn_port=GUNICORN_PORT,
    )
    if all_passed(results):
        emit("[OK] Stage 8 already satisfied — skipping")
        return

    emit(step_header("App config (sections H\u2013H4g)"))

    # Ensure poll_gunicorn.py is on the VM (may be absent if Stage 4 ran
    # before this file was added to tools/vm_scripts/)
    r = scp_to_vm(config, [str(_POLL_GUNICORN)], "/tmp/vm_scripts/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP poll_gunicorn.py failed: {r.stderr.strip()}")

    # SCP both scripts
    scripts = [str(_PRE_RESTART), str(_POST_RESTART)]
    r = scp_to_vm(config, scripts, "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP stage 8 scripts failed: {r.stderr.strip()}")

    # Script 1: pre-restart config (H–H4d)
    emit("  Running pre_restart_config.sh ...")
    cmd = (
        f"sudo bash /tmp/pre_restart_config.sh"
        f" {config.bench_dir} {config.site_url} {config.erp_user}"
        f" {config.erp_user_pwd} {GUNICORN_PORT}"
    )
    r = ssh_run(config, cmd, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(
            f"pre_restart_config.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")

    # Script 2: post-restart config (H4e–H4g)
    emit("  Running post_restart_config.sh ...")
    cmd = (
        f"sudo bash /tmp/post_restart_config.sh"
        f" {config.bench_dir} {config.site_url} {config.erp_user}"
        f" {GUNICORN_PORT}"
    )
    r = ssh_run(config, cmd, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(
            f"post_restart_config.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")
