#!/usr/bin/env python3
"""switch_to_v14 emits NODE_OPTIONS + yes-pipe (Phase 5 plan §4.3)."""

from __future__ import annotations

import sys
from pathlib import Path

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


if __name__ == "__main__":
    sys.exit(0 if test_switch_to_v14_emits_node_options_and_yes_pipe() else 1)
