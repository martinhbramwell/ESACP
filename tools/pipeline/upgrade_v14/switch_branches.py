"""Stage 3 — bench switch-to-branch frappe + erpnext to a target major version.

Runs with NODE_OPTIONS=--max-old-space-size=4096 to survive yarn install.
Uses `yes y |` to auto-answer the destructive-checkout confirmation; `git
checkout -f` silently wipes any in-place core-tree edits, which is exactly
what the staged upgrade plans for (drifts are recreated as DB rows by
Stages 5 + 6).
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def branch_for(version: int) -> str:
    """Map a major version (14, 15, 16) to its frappe/erpnext branch name."""
    return f"version-{version}"


def _on_branch(config: Config, app: str, branch: str) -> bool:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} bash -c "
                f"'cd {config.bench_dir}/apps/{app} && git rev-parse --abbrev-ref HEAD'",
                timeout=20)
    return r.returncode == 0 and branch in r.stdout


def make_switch_stage(version: int):
    """Build the Stage-3 unit that switches frappe+erpnext to ``version``.

    Returns an IoC stage ``(Config, Emit) -> TaskResult`` with the target
    branch bound, so the orchestrator loop stays version-agnostic.
    """
    branch = branch_for(version)

    def switch_to_branch(config: Config, emit: Emit) -> TaskResult:
        if _on_branch(config, "frappe", branch) and _on_branch(config, "erpnext", branch):
            return TaskResult(True, False, f"frappe + erpnext already on {branch}")
        emit(f"  bench switch-to-branch {branch} frappe erpnext --upgrade")
        cmd = (f"yes y | sudo -u {config.erp_user} bash -c "
               f"'cd {config.bench_dir} && NODE_OPTIONS=--max-old-space-size=4096 "
               f"bench switch-to-branch {branch} frappe erpnext --upgrade'")
        r = ssh_run(config, cmd, timeout=1800)
        # #331: `switch-to-branch --upgrade` reinstalls EVERY app via uv, which
        # crashes on the bespoke apps' git-URL deps. frappe+erpnext are switched
        # BEFORE that crash; Stage 4 reinstalls the bespoke apps with --no-deps.
        # The success criterion is therefore the postcondition (both core apps on
        # `branch`), not the exit code.
        if not (_on_branch(config, "frappe", branch) and _on_branch(config, "erpnext", branch)):
            return TaskResult(False, False,
                              f"switch-to-branch failed (frappe/erpnext not on {branch}): "
                              f"{r.stderr[-500:]}")
        if r.returncode != 0:
            emit(f"  ⚠ switch-to-branch exited non-zero — expected #331 bespoke uv "
                 f"crash; frappe+erpnext on {branch}, Stage 4 reinstalls bespoke --no-deps")
        emit(f"  ✓ frappe + erpnext on {branch}")
        return TaskResult(True, True, f"switched to {branch}")

    return switch_to_branch
