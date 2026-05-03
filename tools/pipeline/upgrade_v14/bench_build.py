"""Stage 8 — bench build (rebuild dist assets after V14)."""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def run_bench_build(config: Config, emit: Emit) -> TaskResult:
    emit("  bench build")
    cmd = (f"sudo -u {config.erp_user} bash -c "
           f"'cd {config.bench_dir} && NODE_OPTIONS=--max-old-space-size=4096 bench build'")
    r = ssh_run(config, cmd, timeout=1800)
    if r.returncode != 0:
        return TaskResult(False, False, f"bench build failed: {r.stderr[-500:]}")
    return TaskResult(True, True, "bench build completed")
