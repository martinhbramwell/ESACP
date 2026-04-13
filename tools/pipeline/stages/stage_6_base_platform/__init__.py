"""Stage 6: Base Platform — envars, bench symlink, deploy keys, app clones, supervisor.

Two bash scripts SCP'd to the VM and run via SSH:
  platform_setup.sh   — sections A, A2, A2b, A2c, A2e, B, C
  clone_and_services.sh — sections A2d, A3, A3b, B2b

After clone_and_services.sh, a final SSH command creates the BaRe/envars.sh
symlink (section C depends on BaRe being cloned in A2d).
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_6

_DIR = Path(__file__).parent
_PLATFORM_SETUP = _DIR / "platform_setup.sh"
_CLONE_AND_SERVICES = _DIR / "clone_and_services.sh"


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
    )
    if all_passed(results):
        emit("[OK] Stage 6 already satisfied — skipping")
        return

    emit("── Stage 6: Base platform (sections A–C + B2b) ──")

    # SCP both scripts
    r = scp_to_vm(config, [str(_PLATFORM_SETUP), str(_CLONE_AND_SERVICES)],
                   "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP stage 6 scripts failed: {r.stderr.strip()}")

    # Run platform_setup.sh
    emit("  Running platform_setup.sh ...")
    cmd = (
        f"sudo bash /tmp/platform_setup.sh"
        f" {config.bench_dir} {config.bench_dir_orig} {config.erp_user}"
    )
    r = ssh_run(config, cmd, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(
            f"platform_setup.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")

    # Run clone_and_services.sh
    emit("  Running clone_and_services.sh ...")
    cmd = (
        f"sudo bash /tmp/clone_and_services.sh"
        f" {config.bench_dir} {config.erp_user}"
    )
    r = ssh_run(config, cmd, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(
            f"clone_and_services.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")

    # BaRe/envars.sh symlink — section C depends on BaRe cloned by A2d
    emit("  Linking BaRe/envars.sh ...")
    cmd = (
        f"sudo -u {config.erp_user} ln -sf"
        f" /opt/ce_sri/envars.sh {config.bench_dir}/BaRe/envars.sh"
    )
    r = ssh_run(config, cmd, timeout=15)
    if r.returncode != 0:
        raise RuntimeError(
            f"BaRe/envars.sh symlink failed: {r.stderr.strip()}"
        )
    emit("  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh")
