"""Stage 5 — install the synthetic legacy_error_fixes Frappe app.

Targets the substrate's bench. Uses `bench get-app` from a configurable
URL (LEGACY_APP_REPO env var, defaulting to a local checkout path on the
controller — Session 3.5 must publish to GitHub or scp before E2E).
Idempotent: skipped if already in apps.txt.
"""

from __future__ import annotations

import os

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

APP_NAME = "legacy_error_fixes"
DEFAULT_REPO = "https://github.com/martinhbramwell/legacy_error_fixes.git"


def _installed(config: Config) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} grep -Fxq {APP_NAME} "
                f"{config.bench_dir}/sites/apps.txt && echo Y",
                timeout=15)
    return r.returncode == 0 and "Y" in r.stdout


def install_legacy_app(config: Config, emit: Emit) -> TaskResult:
    if _installed(config):
        return TaskResult(True, False, f"{APP_NAME} already in apps.txt")
    repo = os.environ.get("LEGACY_APP_REPO", DEFAULT_REPO)
    emit(f"  bench get-app {APP_NAME} {repo}")
    get = (f"sudo -u {config.erp_user} bash -c "
           f"'cd {config.bench_dir} && bench get-app --branch main {repo}'")
    r = ssh_run(config, get, timeout=600)
    if r.returncode != 0:
        return TaskResult(False, False, f"bench get-app failed: {r.stderr[-300:]}")
    inst = (f"sudo -u {config.erp_user} bash -c "
            f"'cd {config.bench_dir} && bench --site {config.site_url} install-app {APP_NAME}'")
    r = ssh_run(config, inst, timeout=300)
    if r.returncode != 0:
        return TaskResult(False, False, f"bench install-app failed: {r.stderr[-300:]}")
    return TaskResult(True, True, f"{APP_NAME} installed on {config.site_url}")
