#!/usr/bin/env python3
"""legacy_app_install is idempotent when already in apps.txt."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14.legacy_app_install as legacy_app_install  # noqa: E402
from tools.pipeline.upgrade_v14._test_helpers import make_config, ok, patch_ssh  # noqa: E402


def test_legacy_app_install_is_idempotent() -> bool:
    def fake(_cfg, cmd, *, timeout=30):
        if "grep -Fxq legacy_error_fixes" in cmd:
            return ok("Y\n")
        from types import SimpleNamespace
        return SimpleNamespace(returncode=1, stdout="", stderr="should not be called")

    orig = patch_ssh(legacy_app_install, fake)
    try:
        result = legacy_app_install.install_legacy_app(make_config(), lambda _: None)
    finally:
        legacy_app_install.ssh_run = orig
    if not result.success or result.changed:
        print(f"FAIL: idempotent path returned (success={result.success}, changed={result.changed})")
        return False
    print("PASS: legacy_app_install is idempotent")
    return True


if __name__ == "__main__":
    sys.exit(0 if test_legacy_app_install_is_idempotent() else 1)
