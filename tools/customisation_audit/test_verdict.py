#!/usr/bin/env python3
"""Tests for verdict + promotion-strategy enums.

Pins the string values to the plan §6 contract — Phase 2 + 4 consume these.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit.verdict import PromotionStrategy, Verdict  # noqa: E402


def test_verdict_strings_match_plan() -> None:
    expected = {
        "in_fixture_correct", "drifted", "db_only", "orphan_fixture",
        "discardable_core_edit", "fixture_equivalent_core_edit",
        "human_review_core_edit", "enumerate_only", "informational",
    }
    assert {v.value for v in Verdict} == expected


def test_promotion_strategy_strings_match_plan() -> None:
    expected = {
        "fixture_json", "fixtures_custom_scripts", "app_translations_csv",
        "v14_patch_script", "manual", "none",
    }
    assert {p.value for p in PromotionStrategy} == expected


if __name__ == "__main__":
    test_verdict_strings_match_plan()
    test_promotion_strategy_strings_match_plan()
    print("OK test_verdict")
