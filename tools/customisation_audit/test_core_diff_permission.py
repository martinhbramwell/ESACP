#!/usr/bin/env python3
"""Tests for core_diff_permission — uses real user.json HR Manager fixture."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import core_diff_permission as mod  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures_core_edits"


def test_user_json_emits_two_hr_manager_drifts() -> None:
    diff = (FIX / "user_hr_manager.diff").read_text()
    after = (FIX / "user_after.json").read_text()
    before = (FIX / "user_before.json").read_text()
    out = mod.classify("frappe", "frappe/core/doctype/user/user.json",
                       diff, before, after)
    assert out and len(out) == 2
    assert all(d.verdict == "fixture_equivalent_core_edit" for d in out)
    assert all(d.promotion_strategy == "fixture_json" for d in out)
    assert all(d.row_data.get("role") == "HR Manager" for d in out)
    assert all(d.row_data.get("parent") == "User" for d in out)


def test_no_permission_block_returns_none() -> None:
    out = mod.classify("frappe", "frappe/x.json", "@@\n+ {\n+ \"y\": 1\n+ }\n",
                       "", "{}")
    assert out is None


if __name__ == "__main__":
    test_user_json_emits_two_hr_manager_drifts()
    test_no_permission_block_returns_none()
    print("OK test_core_diff_permission")
