#!/usr/bin/env python3
"""verify_upgrade(config, N) returns 3 checks; all_passed True on green."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14.verify as verify  # noqa: E402
from tools.pipeline.upgrade_v14._test_helpers import make_config, ok, patch_ssh  # noqa: E402


def test_verify_returns_three_checks_all_passing_on_green() -> bool:
    # Green for a v15 target: rev-parse reports version-15, apps.txt grep → Y.
    def fake(_cfg, _cmd, *, timeout=30):
        return ok("version-15\nY\n")

    orig = patch_ssh(verify, fake)
    try:
        results = verify.verify_upgrade(make_config(), 15)
    finally:
        verify.ssh_run = orig
    if len(results) != 3:
        print(f"FAIL: expected 3 verify checks, got {len(results)}")
        return False
    if not verify.all_passed(results):
        print(f"FAIL: all_passed should be True on green: {results}")
        return False
    if "version-15" not in results[0][1]:
        print(f"FAIL: check label not bound to target branch: {results[0][1]}")
        return False
    print("PASS: verify_upgrade(_,15) returns 3 checks; all_passed True on green")
    return True


if __name__ == "__main__":
    sys.exit(0 if test_verify_returns_three_checks_all_passing_on_green() else 1)
