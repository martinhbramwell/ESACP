#!/usr/bin/env python3
"""Tests for drift.Drift + stable_id."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit.drift import Drift, stable_id  # noqa: E402


def test_stable_id_deterministic() -> None:
    a = stable_id("custom_field", "Sales Invoice-foo", "Sales Invoice", "foo")
    b = stable_id("custom_field", "Sales Invoice-foo", "Sales Invoice", "foo")
    assert a == b, "stable_id is not deterministic"
    assert len(a) == 12, f"expected 12-char id, got {len(a)}"


def test_stable_id_distinct_inputs() -> None:
    a = stable_id("custom_field", "X", "Y")
    b = stable_id("property_setter", "X", "Y")
    assert a != b, "stable_id must distinguish drift_class"


def test_drift_dataclass_default_factories() -> None:
    d = Drift(id="x", drift_class="custom_field", verdict="db_only",
              doctype="Sales Invoice", name="X", owning_app_proposed="ce_sri",
              fixture_path_proposed="", promotion_strategy="fixture_json")
    assert d.row_data == {} and d.notes == [] and d.diff is None


if __name__ == "__main__":
    test_stable_id_deterministic()
    test_stable_id_distinct_inputs()
    test_drift_dataclass_default_factories()
    print("OK test_drift")
