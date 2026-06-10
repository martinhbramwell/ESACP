"""Idempotency verifier for the staged upgrade — what's already done?

Per the existing pipeline pattern (verify.py colocated with each stage
package): returns list[(passed, msg)] tuples that the orchestrator can
consult to skip already-completed stages on re-run. Keeps a local
``_on_branch`` (rather than importing switch_branches') so the test can
patch this module's ``ssh_run`` with a single substitution.
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config

from .legacy_app_install import APP_NAME
from .switch_branches import branch_for


def _grep_app_in_apps_txt(config: Config, app: str) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} grep -Fxq {app} "
                f"{config.bench_dir}/sites/apps.txt && echo Y",
                timeout=15)
    return r.returncode == 0 and "Y" in r.stdout


def _on_branch(config: Config, app: str, branch: str) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} bash -c "
                f"'cd {config.bench_dir}/apps/{app} && git rev-parse --abbrev-ref HEAD'",
                timeout=15)
    return r.returncode == 0 and branch in r.stdout


def verify_upgrade(config: Config, target_version: int) -> list[tuple[bool, str]]:
    branch = branch_for(target_version)
    return [
        (_on_branch(config, "frappe", branch), f"apps/frappe on {branch}"),
        (_on_branch(config, "erpnext", branch), f"apps/erpnext on {branch}"),
        (_grep_app_in_apps_txt(config, APP_NAME), f"{APP_NAME} in apps.txt"),
    ]


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(p for p, _ in results)
