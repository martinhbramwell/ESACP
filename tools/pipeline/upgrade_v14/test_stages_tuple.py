#!/usr/bin/env python3
"""Regression guard: STAGES tuple has 10 entries (Phase 5 plan §4.3)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14 as pkg  # noqa: E402


def test_stages_tuple_has_10_entries() -> bool:
    if len(pkg.STAGES) != 10:
        print(f"FAIL: STAGES has {len(pkg.STAGES)} entries, expected 10")
        return False
    print("PASS: STAGES tuple has 10 entries")
    return True


if __name__ == "__main__":
    sys.exit(0 if test_stages_tuple_has_10_entries() else 1)
