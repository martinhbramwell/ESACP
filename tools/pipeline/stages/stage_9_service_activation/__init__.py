"""Stage 9: Service Activation — Social Login, stop.py, bash_aliases.

One bash script SCP'd to the VM and run via SSH:
  service_activation.sh — sections H4a-sl, L0, L

Note: TLS setup (sections I, J, K) is handled by Stage 5.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_9

_DIR = Path(__file__).parent
_SCRIPT = _DIR / "service_activation.sh"
_GENERIC_SCRIPT = _DIR / "generic_activation.sh"


def run_stage_9(config: Config, emit: Emit) -> None:
    """Execute service activation (sections H4a-sl, L0, L).

    Raises
    ------
    RuntimeError
        If any critical step fails.
    """
    results = verify_stage_9(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
        erp_user=config.erp_user,
        bench_dir=config.bench_dir,
        site_url=config.site_url,
    )
    if all_passed(results):
        emit("[OK] Stage 9 already satisfied — skipping")
        return

    script = _GENERIC_SCRIPT if config.provision_mode == "generic" else _SCRIPT
    label = "generic" if config.provision_mode == "generic" else "sections H4a-sl, L0, L"
    emit(step_header(f"Service activation ({label})"))

    r = scp_to_vm(config, [str(script)], "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP {script.name} failed: {r.stderr.strip()}")

    cmd = (
        f"sudo bash /tmp/{script.name}"
        f" {config.bench_dir} {config.site_url} {config.erp_user}"
    )
    r = ssh_run(config, cmd, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(
            f"{script.name} failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")
