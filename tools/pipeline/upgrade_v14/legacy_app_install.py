"""Stage 5 — install the synthetic legacy_error_fixes Frappe app.

The app is a controller-local artifact under $BESPOKE_ROOT (operator decision:
NO GitHub repo — its patches carry tenant field names). It is delivered by
rsync, not `bench get-app <url>`: the local checkout is copied to the VM and
`bench get-app` runs against that local path. The 18 patches it carries
recreate the fixture-equivalent dev-mode drift wiped by the V14 source-tree
checkout. Idempotent: skipped if already in apps.txt.

`LEGACY_APP_SRC` env var overrides the controller source path.
"""

from __future__ import annotations

import os

from tools.bespoke_root import BESPOKE_ROOT
from tools.pipeline.stages.common.ssh import rsync_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

APP_NAME = "legacy_error_fixes"
STAGING = f"/tmp/{APP_NAME}"


def _installed(config: Config) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} grep -Fxq {APP_NAME} "
                f"{config.bench_dir}/sites/apps.txt && echo Y",
                timeout=15)
    return r.returncode == 0 and "Y" in r.stdout


def _installed_on_site(config: Config) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir} && "
                f"bench --site {config.site_url} execute frappe.get_installed_apps'",
                timeout=60)
    return APP_NAME in r.stdout


def _src_path() -> str:
    return os.environ.get("LEGACY_APP_SRC", str(BESPOKE_ROOT / APP_NAME))


def install_legacy_app(config: Config, emit: Emit) -> TaskResult:
    if _installed(config):
        return TaskResult(True, False, f"{APP_NAME} already in apps.txt")
    src = _src_path()
    emit(f"  rsync {src} → {config.hostname}:{STAGING}")
    # A prior run leaves STAGING owned by erp_user; clear it so rsync (run as
    # the SSH user) can rewrite it cleanly.
    ssh_run(config, f"sudo rm -rf {STAGING}", timeout=30)
    r = rsync_to_vm(config, src + "/", STAGING + "/", timeout=120,
                    extra_args=["--delete"])
    if r.returncode != 0:
        return TaskResult(False, False, f"rsync {src} failed: {r.stderr[-300:]}")
    # bench (and its git clone) run as erp_user; the SSH user wrote the staging
    # dir, so hand ownership over or git refuses with "dubious ownership".
    ssh_run(config, f"sudo chown -R {config.erp_user}:{config.erp_user} {STAGING}",
            timeout=30)
    emit(f"  bench get-app {STAGING}")
    get = (f"sudo -u {config.erp_user} bash -c "
           f"'cd {config.bench_dir} && bench get-app {STAGING}'")
    r = ssh_run(config, get, timeout=600)
    if r.returncode != 0:
        return TaskResult(False, False, f"bench get-app failed: {r.stderr[-300:]}")
    inst = (f"sudo -u {config.erp_user} bash -c "
            f"'cd {config.bench_dir} && bench --site {config.site_url} "
            f"install-app {APP_NAME}'")
    r = ssh_run(config, inst, timeout=300)
    # install-app on a switched-but-not-yet-migrated v14 bench prints non-fatal
    # "Error in query: tabDocType State" noise (that table is created by Stage 6
    # migrate) and may exit non-zero, yet still registers the app. Trust the
    # postcondition (site installed_apps); the 18 patches run at Stage 6 migrate.
    if not _installed_on_site(config):
        return TaskResult(False, False, f"install-app failed: {r.stderr[-300:]}")
    if r.returncode != 0:
        emit("  ⚠ install-app exited non-zero (pre-migrate tabDocType State "
             "noise); app registered, patches run at Stage 6 migrate")
    return TaskResult(True, True, f"{APP_NAME} installed on {config.site_url}")
