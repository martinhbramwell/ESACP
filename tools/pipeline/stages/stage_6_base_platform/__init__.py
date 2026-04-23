"""Stage 6: Base Platform — envars, bench symlink, deploy keys, app clones, supervisor.

Two bash orchestrators SCP'd to the VM and run via SSH:
  platform_setup.sh   — sections A, A2, A2b, A2c, A2e, B, C
  clone_and_services.sh — sections A2d (bespoke + BaRe), A3a/b/c, B2b, + re-run C

Section scripts in ``sections/`` are rsynced to ``/tmp/sections/`` and invoked
by the orchestrators via ``bash "$(dirname "$0")/sections/<file>"``.

Both orchestrators accept MODE as final arg (``generic`` | ``restored``).
In generic mode: no ce_sri envars path, no bespoke app clones, no ce_sri_svc
Procfile / supervisor conf / npm install, no you_gh_* deploy keys.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.ssh import rsync_to_vm, scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_6

_DIR = Path(__file__).parent
_PLATFORM_SETUP = _DIR / "platform_setup.sh"
_CLONE_AND_SERVICES = _DIR / "clone_and_services.sh"
_SECTIONS_DIR = _DIR / "sections"


def run_stage_6(config: Config, emit: Emit) -> None:
    """Execute base platform setup (sections A–C + B2b).

    Raises
    ------
    RuntimeError
        If any critical step fails.
    """
    results = verify_stage_6(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
        erp_user=config.erp_user,
        bench_dir=config.bench_dir,
        provision_mode=config.provision_mode,
    )
    if all_passed(results):
        emit("[OK] Stage 6 already satisfied — skipping")
        return

    emit(step_header(f"Base platform ({config.provision_mode} mode)"))

    # SCP both orchestrators and rsync the sections/ dir.
    r = scp_to_vm(config, [str(_PLATFORM_SETUP), str(_CLONE_AND_SERVICES)],
                   "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP stage 6 orchestrators failed: {r.stderr.strip()}")
    r = rsync_to_vm(config, str(_SECTIONS_DIR) + "/", "/tmp/sections/", timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"rsync stage 6 sections failed: {r.stderr.strip()}")

    # Run platform_setup.sh
    emit("  Running platform_setup.sh ...")
    cmd = (
        f"sudo bash /tmp/platform_setup.sh"
        f" {config.bench_dir} {config.bench_dir_orig} {config.erp_user}"
        f" {config.provision_mode}"
    )
    r = ssh_run(config, cmd, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(
            f"platform_setup.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")

    # Run clone_and_services.sh (includes the BaRe symlink re-run at the end)
    emit("  Running clone_and_services.sh ...")
    cmd = (
        f"sudo bash /tmp/clone_and_services.sh"
        f" {config.bench_dir} {config.erp_user} {config.provision_mode}"
    )
    r = ssh_run(config, cmd, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(
            f"clone_and_services.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")
