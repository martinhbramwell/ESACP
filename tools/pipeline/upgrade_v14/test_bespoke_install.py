#!/usr/bin/env python3
"""bespoke_install skips frappe/erpnext + always uses --no-deps (#331)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14.bespoke_install as bespoke_install  # noqa: E402
from tools.pipeline.upgrade_v14._test_helpers import make_config, ok, patch_ssh  # noqa: E402


def test_bespoke_install_skips_core_apps_and_uses_no_deps() -> bool:
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        if "apps.txt" in cmd:
            return ok("frappe\nerpnext\nce_sri\nreturnable\n")
        return ok()

    orig = patch_ssh(bespoke_install, fake)
    try:
        result = bespoke_install.install_bespoke_apps(make_config(), lambda _: None)
    finally:
        bespoke_install.ssh_run = orig
    if not result.success:
        print(f"FAIL: {result.message}")
        return False
    install_cmds = [c for c in captured if "uv pip install" in c]
    if any("apps/frappe" in c or "apps/erpnext" in c for c in install_cmds):
        print(f"FAIL: core app installed via uv pip:\n{install_cmds}")
        return False
    if not all("--no-deps" in c for c in install_cmds):
        print("FAIL: --no-deps missing on at least one install")
        return False
    # #689: must call bare `uv` targeting the venv python, not env/bin/uv
    if any("env/bin/uv" in c for c in install_cmds):
        print(f"FAIL: uses env/bin/uv (does not exist on v14 bench):\n{install_cmds}")
        return False
    if not all("--python env/bin/python" in c for c in install_cmds):
        print("FAIL: --python env/bin/python missing on at least one install")
        return False
    if len(install_cmds) != 2:
        print(f"FAIL: expected 2 bespoke installs, got {len(install_cmds)}")
        return False
    print("PASS: bespoke_install skips frappe/erpnext + uses --no-deps")
    return True


if __name__ == "__main__":
    sys.exit(0 if test_bespoke_install_skips_core_apps_and_uses_no_deps() else 1)
