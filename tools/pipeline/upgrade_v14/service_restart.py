"""Stage 7 — supervisor reload + nginx restart after V14 migrate."""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def restart_services(config: Config, emit: Emit) -> TaskResult:
    emit("  sudo service nginx restart && sudo supervisorctl reload")
    cmd = "sudo service nginx restart && sudo supervisorctl reload"
    r = ssh_run(config, cmd, timeout=120)
    if r.returncode != 0:
        return TaskResult(False, False, f"service restart failed: {r.stderr[-300:]}")
    return TaskResult(True, True, "nginx restarted; supervisord reloaded")
