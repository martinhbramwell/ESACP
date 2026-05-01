#!/usr/bin/env python3
"""Tests for promotion_dispatch — strategy + bespoke-owner gating."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import promotion_dispatch as mod  # noqa: E402


def test_promotable_for_fixture_json_with_bespoke_owner() -> None:
    d = {"promotion_strategy": "fixture_json", "owning_app_proposed": "ce_sri"}
    assert mod.is_promotable(d) is True


def test_not_promotable_for_unknown_strategy() -> None:
    d = {"promotion_strategy": "manual", "owning_app_proposed": "ce_sri"}
    assert mod.is_promotable(d) is False


def test_not_promotable_for_in_core_owner() -> None:
    """in_core drifts defer to Phase 5 patch generator."""
    d = {"promotion_strategy": "fixture_json", "owning_app_proposed": "in_core"}
    assert mod.is_promotable(d) is False


def test_not_promotable_for_not_ours() -> None:
    d = {"promotion_strategy": "fixture_json", "owning_app_proposed": "not_ours"}
    assert mod.is_promotable(d) is False


def test_v14_patch_script_skipped_in_phase_2() -> None:
    """Q5: fixture-tested only in Phase 2; real-data Phase 5."""
    d = {"promotion_strategy": "v14_patch_script", "owning_app_proposed": "ce_sri"}
    assert mod.is_promotable(d) is False


def test_strategy_module_map_complete() -> None:
    expected = {"fixture_json", "fixtures_custom_scripts",
                "app_translations_csv", "v14_patch_script"}
    assert set(mod.STRATEGY_MODULE.keys()) == expected


if __name__ == "__main__":
    test_promotable_for_fixture_json_with_bespoke_owner()
    test_not_promotable_for_unknown_strategy()
    test_not_promotable_for_in_core_owner()
    test_not_promotable_for_not_ours()
    test_v14_patch_script_skipped_in_phase_2()
    test_strategy_module_map_complete()
    print("OK test_promotion_dispatch")
