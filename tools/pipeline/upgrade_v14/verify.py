"""Idempotency verifier for upgrade_v14 — what's already done?

Per the existing pipeline pattern (verify.py colocated with each stage
package): returns list[(passed, msg)] tuples that the orchestrator can
consult to skip already-completed stages on re-run.
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config

from .legacy_app_install import APP_NAME
from .switch_branches import V14_BRANCH


def _grep_app_in_apps_txt(config: Config, app: str) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} grep -Fxq {app} "
                f"{config.bench_dir}/sites/apps.txt && echo Y",
                timeout=15)
    return r.returncode == 0 and "Y" in r.stdout


def _on_v14(config: Config, app: str) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} bash -c "
                f"'cd {config.bench_dir}/apps/{app} && git rev-parse --abbrev-ref HEAD'",
                timeout=15)
    return r.returncode == 0 and V14_BRANCH in r.stdout


def verify_upgrade_v14(config: Config) -> list[tuple[bool, str]]:
    return [
        (_on_v14(config, "frappe"), "apps/frappe on version-14"),
        (_on_v14(config, "erpnext"), "apps/erpnext on version-14"),
        (_grep_app_in_apps_txt(config, APP_NAME), f"{APP_NAME} in apps.txt"),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(p for p, _ in results)
