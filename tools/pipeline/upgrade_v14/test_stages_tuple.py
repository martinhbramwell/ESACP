#!/usr/bin/env python3
"""Regression guard: build_stages(N) has 10 entries + version-bound stage 3."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14 as pkg  # noqa: E402


def test_build_stages_has_10_entries() -> bool:
    if len(pkg.build_stages(14)) != 10:
        print(f"FAIL: build_stages(14) has {len(pkg.build_stages(14))} entries, expected 10")
        return False
    print("PASS: build_stages(14) has 10 entries")
    return True


def test_build_stages_binds_target_version_in_labels() -> bool:
    labels = [label for label, _ in pkg.build_stages(15)]
    if "3 switch-to-version-15" not in labels:
        print(f"FAIL: stage-3 label not bound to v15: {labels}")
        return False
    if "10 acceptance (v15)" not in labels:
        print(f"FAIL: stage-10 label not bound to v15: {labels}")
        return False
    print("PASS: build_stages(15) binds version-15 into stage 3 + 10 labels")
    return True


if __name__ == "__main__":
    ok_all = (
        test_build_stages_has_10_entries()
        and test_build_stages_binds_target_version_in_labels()
    )
    sys.exit(0 if ok_all else 1)
