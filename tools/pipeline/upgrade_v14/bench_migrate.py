"""Stage 6 — bench migrate.

Runs every entry in every installed app's patches.txt, including the 18
legacy_error_fixes patches. Patch Log table tracks idempotency, so a
re-run is safe.
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def run_bench_migrate(config: Config, emit: Emit) -> TaskResult:
    emit(f"  bench --site {config.site_url} migrate")
    cmd = (f"sudo -u {config.erp_user} bash -c "
           f"'cd {config.bench_dir} && bench --site {config.site_url} migrate'")
    r = ssh_run(config, cmd, timeout=3600)
    if r.returncode != 0:
        return TaskResult(False, False, f"bench migrate failed: {r.stderr[-500:]}")
    emit("  ✓ bench migrate exit 0")
    return TaskResult(True, True, "migrate completed")
