#!/usr/bin/env python3
"""make_switch_stage: parametric branch + NODE_OPTIONS + yes-pipe (Phase 5)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14.switch_branches as switch_branches  # noqa: E402
from tools.pipeline.upgrade_v14._test_helpers import make_config, ok, patch_ssh  # noqa: E402


def test_branch_for_maps_major_to_branch() -> bool:
    if not (switch_branches.branch_for(14) == "version-14"
            and switch_branches.branch_for(15) == "version-15"
            and switch_branches.branch_for(16) == "version-16"):
        print("FAIL: branch_for mapping wrong")
        return False
    print("PASS: branch_for maps 14/15/16 → version-N")
    return True


def test_switch_emits_node_options_yes_pipe_and_target_branch() -> bool:
    """The bound branch (here v15) must appear in the switch-to-branch command,
    proving the stage is parameterized rather than hardcoded to v14."""
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        if "rev-parse" in cmd:
            return ok("version-15" if len(captured) > 2 else "version-13")
        return ok()

    orig = patch_ssh(switch_branches, fake)
    try:
        stage = switch_branches.make_switch_stage(15)
        result = stage(make_config(), lambda _: None)
    finally:
        switch_branches.ssh_run = orig
    if not result.success:
        print(f"FAIL: {result.message}")
        return False
    cmd = next((c for c in captured if "switch-to-branch" in c), "")
    if "version-15" not in cmd:
        print(f"FAIL: target branch version-15 missing from command:\n{cmd}")
        return False
    if "NODE_OPTIONS=--max-old-space-size=4096" not in cmd:
        print(f"FAIL: NODE_OPTIONS missing:\n{cmd}")
        return False
    if not cmd.startswith("yes y |"):
        print(f"FAIL: yes-pipe missing:\n{cmd}")
        return False
    print("PASS: make_switch_stage(15) emits version-15 + NODE_OPTIONS + yes-pipe")
    return True


def test_switch_succeeds_on_expected_331_crash() -> bool:
    """#331: switch-to-branch exits non-zero on the bespoke uv crash, but
    frappe+erpnext reach the target — the postcondition, not the exit code."""
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        if "rev-parse" in cmd:
            return ok("version-14" if len(captured) > 2 else "version-13")
        return SimpleNamespace(returncode=1, stdout="", stderr="gunicorn URL dep")

    orig = patch_ssh(switch_branches, fake)
    try:
        stage = switch_branches.make_switch_stage(14)
        result = stage(make_config(), lambda _: None)
    finally:
        switch_branches.ssh_run = orig
    if not result.success:
        print(f"FAIL: stage should succeed when core apps reach target: {result.message}")
        return False
    print("PASS: switch succeeds on expected #331 crash when core apps on target")
    return True


def test_switch_fails_when_core_apps_not_on_target() -> bool:
    """A genuine failure: command errors AND frappe/erpnext never reach target."""
    def fake(_cfg, cmd, *, timeout=30):
        if "rev-parse" in cmd:
            return ok("version-13")
        return SimpleNamespace(returncode=1, stdout="", stderr="real failure")

    orig = patch_ssh(switch_branches, fake)
    try:
        stage = switch_branches.make_switch_stage(15)
        result = stage(make_config(), lambda _: None)
    finally:
        switch_branches.ssh_run = orig
    if result.success:
        print("FAIL: stage should fail when core apps not on target")
        return False
    print("PASS: switch fails when core apps not on target")
    return True


if __name__ == "__main__":
    ok_all = (
        test_branch_for_maps_major_to_branch()
        and test_switch_emits_node_options_yes_pipe_and_target_branch()
        and test_switch_succeeds_on_expected_331_crash()
        and test_switch_fails_when_core_apps_not_on_target()
    )
    sys.exit(0 if ok_all else 1)
