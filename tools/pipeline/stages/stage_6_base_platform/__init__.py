"""Stage 6: Base Platform — envars, bench symlink, deploy keys, app clones, supervisor.

Decomposed into per-section bash scripts (`section_*.sh`) SCP'd to /tmp/ on the
VM and dispatched by two thin orchestrators (`platform_setup.sh`,
`clone_and_services.sh`). Each section is independently runnable; gates on
`PROVISION_MODE` live inside the section, not in the orchestrator.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_6

_DIR = Path(__file__).parent
_PAYLOAD = sorted(str(p) for p in _DIR.glob("*.sh"))


def _run_orchestrator(
    name: str, args: str, config: Config, emit: Emit, timeout: int,
) -> None:
    """SSH-invoke a VM-side orchestrator script and stream its output."""
    cmd = f"sudo bash /tmp/{name} {args}"
    r = ssh_run(config, cmd, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(
            f"{name} failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")


def run_stage_6(config: Config, emit: Emit) -> None:
    """Execute base platform setup (sections A–C + B2b).

    Raises
    ------
    RuntimeError
        If SCP or any orchestrator script fails.
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

    emit(step_header("Base platform (sections A–C + B2b)"))

    r = scp_to_vm(config, _PAYLOAD, "/tmp/", timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"SCP stage 6 scripts failed: {r.stderr.strip()}")

    _run_orchestrator(
        "platform_setup.sh",
        f"{config.bench_dir} {config.bench_dir_orig} {config.erp_user}"
        f" {config.provision_mode}",
        config, emit, timeout=120,
    )
    _run_orchestrator(
        "clone_and_services.sh",
        f"{config.bench_dir} {config.erp_user} {config.provision_mode}",
        config, emit, timeout=300,
    )
