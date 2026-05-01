#!/usr/bin/env python3
"""Tests for core_diff_human_review — non-JSON files + unrecognised JSON shapes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import core_diff_human_review as mod  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures_core_edits"


def test_python_file_classifies_as_human_review() -> None:
    diff = (FIX / "delete_doc.diff").read_text()
    out = mod.classify("frappe", "frappe/model/delete_doc.py", diff, "", "")
    assert out and len(out) == 1
    assert out[0].verdict == "human_review_core_edit"
    assert out[0].promotion_strategy == "manual"
    assert out[0].notes == ["non-JSON"]


def test_unrecognised_json_classifies_as_human_review() -> None:
    out = mod.classify("frappe", "frappe/x.json", "@@", "", "")
    assert out and out[0].notes == ["JSON shape unrecognised"]


if __name__ == "__main__":
    test_python_file_classifies_as_human_review()
    test_unrecognised_json_classifies_as_human_review()
    print("OK test_core_diff_human_review")
