"""Stage 3 — bench switch-to-branch frappe + erpnext to version-14.

Runs with NODE_OPTIONS=--max-old-space-size=4096 to survive yarn install.
Uses `yes y |` to auto-answer the destructive-checkout confirmation; `git
checkout -f` silently wipes any in-place core-tree edits, which is exactly
what Phase 5 plans for (drifts are recreated as DB rows by Stages 5 + 6).
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

V14_BRANCH = "version-14"


def _on_v14(config: Config, app: str) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} bash -c "
                f"'cd {config.bench_dir}/apps/{app} && git rev-parse --abbrev-ref HEAD'",
                timeout=20)
    return r.returncode == 0 and V14_BRANCH in r.stdout


def switch_to_v14(config: Config, emit: Emit) -> TaskResult:
    if _on_v14(config, "frappe") and _on_v14(config, "erpnext"):
        return TaskResult(True, False, "frappe + erpnext already on version-14")
    emit("  bench switch-to-branch version-14 frappe erpnext --upgrade")
    cmd = (f"yes y | sudo -u {config.erp_user} bash -c "
           f"'cd {config.bench_dir} && NODE_OPTIONS=--max-old-space-size=4096 "
           f"bench switch-to-branch version-14 frappe erpnext --upgrade'")
    r = ssh_run(config, cmd, timeout=1800)
    if r.returncode != 0:
        return TaskResult(False, False, f"switch-to-branch failed: {r.stderr[-500:]}")
    if not (_on_v14(config, "frappe") and _on_v14(config, "erpnext")):
        return TaskResult(False, False, "post-switch branch check failed")
    emit("  ✓ frappe + erpnext on version-14")
    return TaskResult(True, True, "switched to version-14")
