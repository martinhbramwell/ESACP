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


def test_legacy_app_install_delivers_by_rsync_local_path() -> bool:
    """Not yet installed → rsync the controller checkout, then bench get-app
    from the LOCAL staging path (no GitHub URL) + install-app."""
    from types import SimpleNamespace
    calls = {"rsync": 0}

    def fake_rsync(_cfg, local, remote, *, timeout=30, extra_args=None):
        calls["rsync"] += 1
        calls["rsync_local"] = local
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    captured: list[str] = []

    def fake_ssh(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        if "grep -Fxq legacy_error_fixes" in cmd:
            return SimpleNamespace(returncode=1, stdout="", stderr="")  # not installed
        if "get_installed_apps" in cmd:  # postcondition: app registered on site
            return ok("['frappe', 'legacy_error_fixes', 'erpnext']")
        return ok()

    orig_ssh = patch_ssh(legacy_app_install, fake_ssh)
    orig_rsync = legacy_app_install.rsync_to_vm
    legacy_app_install.rsync_to_vm = fake_rsync
    try:
        result = legacy_app_install.install_legacy_app(make_config(), lambda _: None)
    finally:
        legacy_app_install.ssh_run = orig_ssh
        legacy_app_install.rsync_to_vm = orig_rsync

    if not (result.success and result.changed):
        print(f"FAIL: delivery path (success={result.success}, changed={result.changed})")
        return False
    if calls["rsync"] != 1:
        print(f"FAIL: expected one rsync, got {calls['rsync']}")
        return False
    get = next((c for c in captured if "bench get-app" in c), "")
    if "legacy_error_fixes" not in get or "http" in get:
        print(f"FAIL: get-app should target local staging path, not a URL:\n{get}")
        return False
    if not any("install-app legacy_error_fixes" in c for c in captured):
        print("FAIL: install-app not invoked")
        return False
    print("PASS: legacy_app_install delivers by rsync + local-path get-app")
    return True


def test_install_succeeds_on_premigrate_noise_when_app_registered() -> bool:
    """install-app exits non-zero (pre-migrate tabDocType State noise) but the
    app IS in site installed_apps → postcondition decides success."""
    from types import SimpleNamespace

    def fake_rsync(_cfg, local, remote, *, timeout=30, extra_args=None):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_ssh(_cfg, cmd, *, timeout=30):
        if "grep -Fxq legacy_error_fixes" in cmd:
            return SimpleNamespace(returncode=1, stdout="", stderr="")  # not installed
        if "get_installed_apps" in cmd:
            return ok("['frappe', 'legacy_error_fixes']")  # registered despite noise
        if "install-app" in cmd:
            return SimpleNamespace(returncode=1, stdout="", stderr="Error in query")
        return ok()

    orig_ssh = patch_ssh(legacy_app_install, fake_ssh)
    orig_rsync = legacy_app_install.rsync_to_vm
    legacy_app_install.rsync_to_vm = fake_rsync
    try:
        result = legacy_app_install.install_legacy_app(make_config(), lambda _: None)
    finally:
        legacy_app_install.ssh_run = orig_ssh
        legacy_app_install.rsync_to_vm = orig_rsync
    if not result.success:
        print(f"FAIL: should succeed when app registered despite noise: {result.message}")
        return False
    print("PASS: install succeeds on pre-migrate noise when app registered")
    return True


if __name__ == "__main__":
    ok_all = (
        test_legacy_app_install_is_idempotent()
        and test_legacy_app_install_delivers_by_rsync_local_path()
        and test_install_succeeds_on_premigrate_noise_when_app_registered()
    )
    sys.exit(0 if ok_all else 1)
