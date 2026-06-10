"""Stage 9 — disable maintenance, resume scheduler."""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def resume_scheduler(config: Config, emit: Emit) -> TaskResult:
    emit(f"  bench --site {config.site_url} set-maintenance-mode off + schedule resume")
    # Both subcommands need --site: V15 dropped the currentsite.txt default-site
    # fallback, so a bare `bench scheduler resume` exits 1 ("Please specify
    # --site") — and prints that to stdout, not stderr, hence surface both.
    cmds = [
        f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir} && "
        f"bench --site {config.site_url} set-maintenance-mode off'",
        f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir} && "
        f"bench --site {config.site_url} scheduler resume'",
    ]
    for cmd in cmds:
        r = ssh_run(config, cmd, timeout=60)
        if r.returncode != 0:
            return TaskResult(False, False,
                              f"scheduler resume failed: {(r.stderr or r.stdout)[-300:]}")
    return TaskResult(True, True, "maintenance off; scheduler resumed")
