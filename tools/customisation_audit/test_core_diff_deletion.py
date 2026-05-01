#!/usr/bin/env python3
"""Tests for core_diff_deletion — party_type-shape + auto-resave-only."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import core_diff_deletion as mod  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures_core_edits"


def test_party_type_classifies_as_discardable() -> None:
    diff = (FIX / "party_type.diff").read_text()
    before = (FIX / "party_type_before.json").read_text()
    after = (FIX / "party_type_after.json").read_text()
    out = mod.classify("erpnext", "erpnext/setup/doctype/party_type/party_type.json",
                       diff, before, after)
    assert out and len(out) == 1
    assert out[0].verdict == "discardable_core_edit"
    assert out[0].promotion_strategy == "none"


def test_auto_resave_only_classifies_as_discardable() -> None:
    before = '{"name": "X", "modified": "2020-01-01"}'
    after = '{"name": "X", "modified": "2024-01-01"}'
    diff = '@@ @@\n- "modified": "2020-01-01"\n+ "modified": "2024-01-01"\n'
    out = mod.classify("frappe", "frappe/x.json", diff, before, after)
    assert out and len(out) == 1 and out[0].verdict == "discardable_core_edit"


def test_user_with_new_perm_returns_none() -> None:
    diff = (FIX / "user_hr_manager.diff").read_text()
    before = (FIX / "user_before.json").read_text()
    after = (FIX / "user_after.json").read_text()
    out = mod.classify("frappe", "frappe/core/doctype/user/user.json",
                       diff, before, after)
    assert out is None


if __name__ == "__main__":
    test_party_type_classifies_as_discardable()
    test_auto_resave_only_classifies_as_discardable()
    test_user_with_new_perm_returns_none()
    print("OK test_core_diff_deletion")
