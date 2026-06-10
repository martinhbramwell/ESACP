#!/usr/bin/env python3
"""switch_to_v14 emits NODE_OPTIONS + yes-pipe (Phase 5 plan §4.3)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14.switch_branches as switch_branches  # noqa: E402
from tools.pipeline.upgrade_v14._test_helpers import make_config, ok, patch_ssh  # noqa: E402


def test_switch_to_v14_emits_node_options_and_yes_pipe() -> bool:
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        if "rev-parse" in cmd:
            return ok("version-14" if len(captured) > 2 else "version-13")
        return ok()

    orig = patch_ssh(switch_branches, fake)
    try:
        result = switch_branches.switch_to_v14(make_config(), lambda _: None)
    finally:
        switch_branches.ssh_run = orig
    if not result.success:
        print(f"FAIL: {result.message}")
        return False
    cmd = next((c for c in captured if "switch-to-branch" in c), "")
    if "NODE_OPTIONS=--max-old-space-size=4096" not in cmd:
        print(f"FAIL: NODE_OPTIONS missing:\n{cmd}")
        return False
    if not cmd.startswith("yes y |"):
        print(f"FAIL: yes-pipe missing:\n{cmd}")
        return False
    print("PASS: switch_to_v14 emits NODE_OPTIONS + yes-pipe")
    return True


def test_switch_to_v14_succeeds_on_expected_331_crash() -> bool:
    """#331: switch-to-branch exits non-zero on the bespoke uv crash, but
    frappe+erpnext reach v14 — the postcondition, not the exit code, decides."""
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        if "rev-parse" in cmd:
            # initial guard short-circuits after frappe (call 1, v13); the
            # post-switch checks are calls 3 (frappe) + 4 (erpnext) → v14
            return ok("version-14" if len(captured) > 2 else "version-13")
        # the switch-to-branch itself exits non-zero (the #331 uv crash)
        return SimpleNamespace(returncode=1, stdout="", stderr="gunicorn URL dep")

    orig = patch_ssh(switch_branches, fake)
    try:
        result = switch_branches.switch_to_v14(make_config(), lambda _: None)
    finally:
        switch_branches.ssh_run = orig
    if not result.success:
        print(f"FAIL: stage should succeed when core apps reach v14: {result.message}")
        return False
    print("PASS: switch_to_v14 succeeds on expected #331 crash when core apps on v14")
    return True


def test_switch_to_v14_fails_when_core_apps_not_on_v14() -> bool:
    """A genuine failure: command errors AND frappe/erpnext never reach v14."""
    def fake(_cfg, cmd, *, timeout=30):
        if "rev-parse" in cmd:
            return ok("version-13")
        return SimpleNamespace(returncode=1, stdout="", stderr="real failure")

    orig = patch_ssh(switch_branches, fake)
    try:
        result = switch_branches.switch_to_v14(make_config(), lambda _: None)
    finally:
        switch_branches.ssh_run = orig
    if result.success:
        print("FAIL: stage should fail when core apps not on v14")
        return False
    print("PASS: switch_to_v14 fails when core apps not on v14")
    return True


if __name__ == "__main__":
    ok_all = (
        test_switch_to_v14_emits_node_options_and_yes_pipe()
        and test_switch_to_v14_succeeds_on_expected_331_crash()
        and test_switch_to_v14_fails_when_core_apps_not_on_v14()
    )
    sys.exit(0 if ok_all else 1)
