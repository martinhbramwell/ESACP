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


def test_v14_patch_script_promotable_with_bespoke_owner() -> None:
    """Phase 5 (Q5 lifted): v14_patch_script with bespoke owner promotes."""
    d = {"promotion_strategy": "v14_patch_script", "owning_app_proposed": "ce_sri"}
    assert mod.is_promotable(d) is True


def test_v14_patch_script_promotable_for_in_core_owner() -> None:
    """in_core drifts route to the synthetic legacy_error_fixes app — promotable."""
    d = {"promotion_strategy": "v14_patch_script", "owning_app_proposed": "in_core"}
    assert mod.is_promotable(d) is True


def test_v14_patch_script_promotable_for_empty_owner() -> None:
    """Empty owner falls back to legacy_error_fixes — promotable."""
    d = {"promotion_strategy": "v14_patch_script", "owning_app_proposed": ""}
    assert mod.is_promotable(d) is True


def test_v14_patch_script_not_promotable_for_not_ours() -> None:
    """not_ours = explicit no-op even for v14_patch_script."""
    d = {"promotion_strategy": "v14_patch_script", "owning_app_proposed": "not_ours"}
    assert mod.is_promotable(d) is False


def test_v14_patch_script_not_promotable_for_synthetic_doctype() -> None:
    """Drifts with synthetic doctypes like '(translation_csv)' are not Frappe rows."""
    d = {"promotion_strategy": "v14_patch_script", "owning_app_proposed": "in_core",
         "doctype": "(translation_csv)"}
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
    test_v14_patch_script_promotable_with_bespoke_owner()
    test_v14_patch_script_promotable_for_in_core_owner()
    test_v14_patch_script_promotable_for_empty_owner()
    test_v14_patch_script_not_promotable_for_not_ours()
    test_v14_patch_script_not_promotable_for_synthetic_doctype()
    test_strategy_module_map_complete()
    print("OK test_promotion_dispatch")
