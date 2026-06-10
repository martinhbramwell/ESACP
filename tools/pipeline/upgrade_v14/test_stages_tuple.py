#!/usr/bin/env python3
"""Regression guard: build_stages(N) has 11 entries + version-bound stages."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14 as pkg  # noqa: E402


def test_build_stages_has_11_entries() -> bool:
    if len(pkg.build_stages(14)) != 11:
        print(f"FAIL: build_stages(14) has {len(pkg.build_stages(14))} entries, expected 11")
        return False
    print("PASS: build_stages(14) has 11 entries")
    return True


def test_build_stages_binds_target_version_in_labels() -> bool:
    labels = [label for label, _ in pkg.build_stages(15)]
    for needed in ("3 switch-to-version-15",
                   "10 post-migrate fixups (v15)",
                   "11 acceptance (v15)"):
        if needed not in labels:
            print(f"FAIL: label {needed!r} missing from v15 stages: {labels}")
            return False
    print("PASS: build_stages(15) binds version-15 into stages 3, 10, 11")
    return True


if __name__ == "__main__":
    ok_all = (
        test_build_stages_has_11_entries()
        and test_build_stages_binds_target_version_in_labels()
    )
    sys.exit(0 if ok_all else 1)
