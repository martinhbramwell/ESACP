"""Stage 5 — install the synthetic legacy_error_fixes Frappe app.
Tenant work in LogiSoluValidations/audit/ beside the catalogue it is generated
from (operator decision: tenant version control, NOT a dedicated repo). Delivered
by rsync to a staging path made into a throwaway git repo (bench get-app needs a
clonable repo; at source it is an LSV subdir). 18 patches recreate the dev-mode
drift wiped by the V14 source checkout. `LEGACY_APP_SRC` overrides source.
"""

from __future__ import annotations

import os

from tools.bespoke_root import BESPOKE_ROOT
from tools.pipeline.stages.common.ssh import rsync_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

APP_NAME = "legacy_error_fixes"
STAGING = f"/tmp/{APP_NAME}"


def _installed(config: Config) -> bool:
    r = ssh_run(config, f"sudo -u {config.erp_user} grep -Fxq {APP_NAME} "
                f"{config.bench_dir}/sites/apps.txt && echo Y", timeout=15)
    return r.returncode == 0 and "Y" in r.stdout


def _installed_on_site(config: Config) -> bool:
    r = ssh_run(config, f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir} "
                f"&& bench --site {config.site_url} execute frappe.get_installed_apps'",
                timeout=60)
    return APP_NAME in r.stdout


def _src_path() -> str:
    d = BESPOKE_ROOT / "LogiSoluValidations" / "audit" / APP_NAME
    return os.environ.get("LEGACY_APP_SRC", str(d))


def _stage_to_vm(config: Config, emit: Emit) -> TaskResult | None:
    """rsync source app to VM, make staging a git repo. None = ok, else fail."""
    src = _src_path()
    emit(f"  rsync {src} → {config.hostname}:{STAGING}")
    ssh_run(config, f"sudo rm -rf {STAGING}", timeout=30)  # clear prior erp_user-owned copy
    r = rsync_to_vm(config, src + "/", STAGING + "/", timeout=120, extra_args=["--delete"])
    if r.returncode != 0:
        return TaskResult(False, False, f"rsync {src} failed: {r.stderr[-300:]}")
    ssh_run(config, f"sudo chown -R {config.erp_user}:{config.erp_user} {STAGING}", timeout=30)
    init = (f"sudo -u {config.erp_user} bash -c 'cd {STAGING} && rm -rf .git && "
            f"git init -q && git add -A && git -c user.email=esacp@local "
            f"-c user.name=esacp commit -qm staged'")
    r = ssh_run(config, init, timeout=60)  # bench get-app needs a clonable repo
    if r.returncode != 0:
        return TaskResult(False, False, f"git init staging failed: {r.stderr[-300:]}")
    return None


def install_legacy_app(config: Config, emit: Emit) -> TaskResult:
    if _installed(config):
        return TaskResult(True, False, f"{APP_NAME} already in apps.txt")
    staged = _stage_to_vm(config, emit)
    if staged is not None:
        return staged
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
    # install-app pre-migrate emits non-fatal "tabDocType State" noise (#690) and
    # may exit non-zero while still registering the app — trust the postcondition.
    if not _installed_on_site(config):
        return TaskResult(False, False, f"install-app failed: {r.stderr[-300:]}")
    if r.returncode != 0:
        emit("  ⚠ install-app exited non-zero (pre-migrate tabDocType State "
             "noise); app registered, patches run at Stage 6 migrate")
    return TaskResult(True, True, f"{APP_NAME} installed on {config.site_url}")
