#!/usr/bin/env python3
"""Tests for drift_builder.db_only + orphan_fixture."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import drift_builder  # noqa: E402
from tools.customisation_audit.verdict import PromotionStrategy  # noqa: E402


def test_db_only_with_owning_app_uses_strategy() -> None:
    row = {"name": "X", "dt": "Sales Invoice", "fieldname": "f", "module": "CE-SRI"}
    d = drift_builder.db_only("custom_field", "Custom Field", row, ("dt", "fieldname"),
                              {"CE-SRI": "ce_sri"}, PromotionStrategy.FIXTURE_JSON)
    assert d.verdict == "db_only"
    assert d.owning_app_proposed == "ce_sri"
    assert d.promotion_strategy == "fixture_json"


def test_db_only_unknown_module_falls_back_to_manual() -> None:
    row = {"name": "X", "module": "ERPNext"}
    d = drift_builder.db_only("custom_field", "Custom Field", row, (),
                              {}, PromotionStrategy.FIXTURE_JSON)
    assert d.owning_app_proposed == ""
    assert d.promotion_strategy == "manual"


def test_orphan_fixture_emitted_with_app() -> None:
    entry = {"name": "X", "dt": "Sales Invoice", "fieldname": "f"}
    d = drift_builder.orphan_fixture("custom_field", "Custom Field", "X", "ce_sri",
                                     entry, ("dt", "fieldname"))
    assert d.verdict == "orphan_fixture"
    assert d.owning_app_proposed == "ce_sri"
    assert d.promotion_strategy == "none"


if __name__ == "__main__":
    test_db_only_with_owning_app_uses_strategy()
    test_db_only_unknown_module_falls_back_to_manual()
    test_orphan_fixture_emitted_with_app()
    print("OK test_drift_builder")
