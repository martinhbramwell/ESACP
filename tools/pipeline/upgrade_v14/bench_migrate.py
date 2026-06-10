"""Stage 6 — bench migrate.

Runs every entry in every installed app's patches.txt, including the 18
legacy_error_fixes patches. Patch Log table tracks idempotency, so a
re-run is safe.
"""

from __future__ import annotations

import os

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def _pause_writers(config: Config, emit: Emit) -> None:
    """#691: quiesce concurrent DB writers before migrate. The background
    WORKERS (default/long/short) hold row locks and make migrate die with
    'Lock wait timeout exceeded' (1205); pausing only the scheduler is NOT
    enough — stop the whole worker supervisor group (proven on dev01). Stage 7's
    `supervisorctl reload` restarts them. Group name = <bench>-workers, derived
    from the real bench dir (not hardcoded)."""
    workers = f"{os.path.basename(config.bench_dir_orig)}-workers:"
    emit(f"  set-maintenance-mode on + stop {workers} (avoid lock contention)")
    for cmd in (
        f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir} && "
        f"bench --site {config.site_url} set-maintenance-mode on'",
        f"sudo supervisorctl stop {workers}",
    ):
        ssh_run(config, cmd, timeout=120)


def run_bench_migrate(config: Config, emit: Emit) -> TaskResult:
    _pause_writers(config, emit)
    emit(f"  bench --site {config.site_url} migrate")
    cmd = (f"sudo -u {config.erp_user} bash -c "
           f"'cd {config.bench_dir} && bench --site {config.site_url} migrate'")
    r = ssh_run(config, cmd, timeout=3600)
    if r.returncode != 0:
        return TaskResult(False, False, f"bench migrate failed: {r.stderr[-500:]}")
    emit("  ✓ bench migrate exit 0")
    return TaskResult(True, True, "migrate completed")
