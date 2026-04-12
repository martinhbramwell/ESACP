"""Stage 5: TLS — cert install, nginx vhost, DH params, site enable.

SCP ``tls_setup.sh`` to the VM and run it via SSH.  The bash script
handles sections I (cert install), J (nginx vhost), K (DH params +
enable).  Extracted from the differentiate.sh generator in api.py.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import scp_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit

from .verify import all_passed, verify_stage_5

_SCRIPT = Path(__file__).parent / "tls_setup.sh"


def run_stage_5(config: Config, emit: Emit) -> None:
    """Execute TLS setup (sections I, J, K).

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
    results = verify_stage_5(
        target_ip=config.target_ip,
        ssh_opts=config.ssh_opts,
        ssh_key=config.ssh_key,
        site_url=config.site_url,
        domain=config.domain,
    )
    if all_passed(results):
        emit("[OK] Stage 5 already satisfied — skipping")
        return

    # ── SCP tls_setup.sh to VM ──
    emit("── Stage 5: TLS setup (sections I, J, K) ──")
    r = scp_to_vm(config, [str(_SCRIPT)], "/tmp/", timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"SCP tls_setup.sh failed: {r.stderr.strip()}")

    # ── Run the script on VM ──
    cmd = f"sudo bash /tmp/tls_setup.sh {config.site_url} {config.domain}"
    r = ssh_run(config, cmd, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(
            f"tls_setup.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")
