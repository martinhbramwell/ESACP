#!/usr/bin/env python3
"""Tests for core_diff_translation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import core_diff_translation as mod  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures_core_edits"


def test_csv_under_translations_classifies_as_translation() -> None:
    diff = (FIX / "translations_es.diff").read_text()
    out = mod.classify("erpnext", "erpnext/translations/es.csv", diff, "", "")
    assert out and len(out) == 1
    d = out[0]
    assert d.verdict == "fixture_equivalent_core_edit"
    assert d.promotion_strategy == "app_translations_csv"


def test_non_translation_path_returns_none() -> None:
    out = mod.classify("frappe", "frappe/something.csv", "diff", "", "")
    assert out is None


if __name__ == "__main__":
    test_csv_under_translations_classifies_as_translation()
    test_non_translation_path_returns_none()
    print("OK test_core_diff_translation")
