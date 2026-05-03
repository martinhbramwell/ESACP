"""Strategy → promote_*.py module dispatcher for Phase 2 (#327)."""

from __future__ import annotations

from pathlib import Path

from tools.customisation_audit import (
    promote_app_translations_csv,
    promote_common,
    promote_fixture_json,
    promote_fixtures_custom_scripts,
    promote_v14_patch_script,
)

STRATEGY_MODULE = {
    "fixture_json": promote_fixture_json,
    "fixtures_custom_scripts": promote_fixtures_custom_scripts,
    "app_translations_csv": promote_app_translations_csv,
    "v14_patch_script": promote_v14_patch_script,
}


def is_promotable(drift) -> bool:
    """True if a fixture/patch should be written for this drift now.

    Phase 5 (Q5 lifted): v14_patch_script accepts in_core/empty owners —
    they route to the synthetic `legacy_error_fixes` Frappe app via
    `promote_v14_patch_script.resolve_v14_patch_app()`. Other strategies
    still require a real bespoke owner (in_core/not_ours skipped).
    """
    strategy = drift.get("promotion_strategy") if isinstance(drift, dict) else getattr(drift, "promotion_strategy", "")
    if strategy not in STRATEGY_MODULE:
        return False
    if strategy == "v14_patch_script":
        # Synthetic doctypes like "(translation_csv)" are not Frappe DB rows;
        # skip them — translation CSVs are operator-handled per Phase 5 plan §3.
        doctype = drift.get("doctype") if isinstance(drift, dict) else getattr(drift, "doctype", "")
        if isinstance(doctype, str) and doctype.startswith("("):
            return False
        owning = drift.get("owning_app_proposed") if isinstance(drift, dict) else getattr(drift, "owning_app_proposed", "")
        return owning != "not_ours"
    return promote_common.is_bespoke_writable(drift)


def target(drift) -> Path:
    return STRATEGY_MODULE[_strategy(drift)].target(drift)


def apply(drift) -> Path:
    return STRATEGY_MODULE[_strategy(drift)].apply(drift)


def _strategy(drift) -> str:
    return drift["promotion_strategy"] if isinstance(drift, dict) else drift.promotion_strategy
