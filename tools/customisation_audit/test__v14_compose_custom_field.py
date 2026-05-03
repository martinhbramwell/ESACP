#!/usr/bin/env python3
"""Tests for _v14_compose_custom_field — fields[X] in-core edit shape."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import _v14_compose_custom_field as mod  # noqa: E402


def _drift() -> dict:
    return {
        "drift_class": "in_place_core_edit",
        "doctype": "Property Setter",
        "name": "erpnext/erpnext/.../address.json#fields[barrio]",
        "row_data": {
            "doctype_or_field": "DocType", "doc_type": "Address",
            "property": "fields[barrio]",
            "value": {"fieldname": "barrio", "fieldtype": "Data", "label": "Barrio"},
        },
    }


def test_matches_fields_x_property() -> None:
    assert mod.matches(_drift()) is True


def test_does_not_match_top_level_property() -> None:
    d = _drift()
    d["row_data"] = {**d["row_data"], "property": "naming_rule"}
    assert mod.matches(d) is False


def test_does_not_match_non_in_place_drift() -> None:
    d = _drift()
    d["drift_class"] = "fixture_match"
    assert mod.matches(d) is False


def test_compose_emits_valid_python() -> None:
    ast.parse(mod.compose(_drift()))


def test_compose_uses_dt_fieldname_idempotency_guard() -> None:
    src = mod.compose(_drift())
    assert "frappe.db.exists('Custom Field'" in src
    assert "'dt': 'Address'" in src
    assert "'fieldname': 'barrio'" in src


def test_compose_emits_custom_field_doctype() -> None:
    src = mod.compose(_drift())
    assert '"doctype": "Custom Field"' in src
    assert '"dt": "Address"' in src
    assert '"fieldtype": "Data"' in src
    assert '"label": "Barrio"' in src


if __name__ == "__main__":
    test_matches_fields_x_property()
    test_does_not_match_top_level_property()
    test_does_not_match_non_in_place_drift()
    test_compose_emits_valid_python()
    test_compose_uses_dt_fieldname_idempotency_guard()
    test_compose_emits_custom_field_doctype()
    print("OK test__v14_compose_custom_field")
