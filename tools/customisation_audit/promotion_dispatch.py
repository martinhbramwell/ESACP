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
    """True if Phase 2 should write a fixture/patch for this drift now.

    Skips: non-promotable strategies, in_core/not_ours owners (deferred to
    Phase 5 patch generator and not_ours = explicit no-op).
    """
    strategy = drift.get("promotion_strategy") if isinstance(drift, dict) else getattr(drift, "promotion_strategy", "")
    if strategy not in STRATEGY_MODULE:
        return False
    if strategy == "v14_patch_script":
        # Q5: fixture-tested only in Phase 2; real-data Phase 5.
        return False
    return promote_common.is_bespoke_writable(drift)


def target(drift) -> Path:
    return STRATEGY_MODULE[_strategy(drift)].target(drift)


def apply(drift) -> Path:
    return STRATEGY_MODULE[_strategy(drift)].apply(drift)


def _strategy(drift) -> str:
    return drift["promotion_strategy"] if isinstance(drift, dict) else drift.promotion_strategy
