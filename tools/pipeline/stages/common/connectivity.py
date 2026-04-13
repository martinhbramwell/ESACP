"""Gate task — fail fast if target VM is unreachable."""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def ensure_connectivity(config: Config, emit: Emit) -> TaskResult:
    """SSH to the target and run ``echo ready``."""
    try:
        r = ssh_run(config, "echo ready", timeout=15)
    except Exception as exc:
        return TaskResult(False, False, f"SSH error: {exc}")
    if r.returncode != 0:
        return TaskResult(False, False,
                          f"SSH failed (exit {r.returncode}): {r.stderr.strip()}")
    return TaskResult(True, False, f"{config.target_ip} reachable")
