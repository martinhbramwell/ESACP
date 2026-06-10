"""Stage 4 — uv pip install --no-deps for bespoke apps after switch-to-v14.

#331 fix: `bench switch-to-branch` invokes `uv pip install -e <bespoke>`,
which crashes on Frappe v14's gunicorn URL dependency. Workaround: install
each bespoke app explicitly with `--no-deps` (frappe's own deps are already
installed by Stage 3). Per CLAUDE.md "no third-party code modification" —
we don't patch frappe's gunicorn spec; we side-step uv's resolver.
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

CORE_APPS = {"frappe", "erpnext"}


def _bespoke_apps(config: Config) -> list[str]:
    r = ssh_run(config,
                f"sudo -u {config.erp_user} cat {config.bench_dir}/sites/apps.txt",
                timeout=15)
    if r.returncode != 0:
        return []
    return [a.strip() for a in r.stdout.splitlines()
            if a.strip() and a.strip() not in CORE_APPS]


def install_bespoke_apps(config: Config, emit: Emit) -> TaskResult:
    apps = _bespoke_apps(config)
    if not apps:
        return TaskResult(True, False, "No bespoke apps in apps.txt — nothing to install")
    emit(f"  uv pip install --no-deps -e for {len(apps)} bespoke apps: {apps}")
    failures: list[str] = []
    for app in apps:
        # #689: uv is installed globally (/usr/local/bin/uv), not in the bench
        # venv — call bare `uv` from PATH and point it at the venv python, as
        # the bench itself and #331's documented workaround do.
        cmd = (f"sudo -u {config.erp_user} bash -c "
               f"'cd {config.bench_dir} && uv pip install --no-deps -e apps/{app} "
               f"--python env/bin/python'")
        r = ssh_run(config, cmd, timeout=300)
        if r.returncode != 0:
            failures.append(f"{app}: {r.stderr[-200:].strip()}")
        else:
            emit(f"    ✓ {app}")
    if failures:
        return TaskResult(False, False, f"uv pip install failures: {failures}")
    return TaskResult(True, True, f"Installed {len(apps)} bespoke apps with --no-deps")
