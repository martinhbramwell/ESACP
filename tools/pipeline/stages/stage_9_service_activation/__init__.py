"""Stage 9: Service Activation — Social Login, stop.py, bash_aliases.

One bash script SCP'd to the VM and run via SSH:
  service_activation.sh — sections H4a-sl, L0, L

Note: TLS setup (sections I, J, K) is handled by Stage 5.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_9

_SCRIPT = Path(__file__).parent / "service_activation.sh"


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

    emit("── Stage 9: Service activation (sections H4a-sl, L0, L) ──")

    r = scp_to_vm(config, [str(_SCRIPT)], "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP service_activation.sh failed: {r.stderr.strip()}")

    cmd = (
        f"sudo bash /tmp/service_activation.sh"
        f" {config.bench_dir} {config.site_url} {config.erp_user}"
    )
    r = ssh_run(config, cmd, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(
            f"service_activation.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")
