#!/usr/bin/env python3
"""Tests for _v14_compose_property_setter — generic fallback shape."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import _v14_compose_property_setter as mod  # noqa: E402


def _drift() -> dict:
    return {
        "drift_class": "property_setter",
        "doctype": "Property Setter",
        "name": "Sales Order-naming_series-options",
        "row_data": {
            "name": "Sales Order-naming_series-options",
            "doctype_or_field": "DocType", "doc_type": "Sales Order",
            "property": "naming_series", "value": "SO-",
        },
    }


def test_matches_property_setter() -> None:
    assert mod.matches(_drift()) is True


def test_does_not_match_other_doctype() -> None:
    d = _drift()
    d["doctype"] = "Translation"
    assert mod.matches(d) is False


def test_compose_emits_valid_python() -> None:
    ast.parse(mod.compose(_drift()))


def test_compose_uses_doctype_name_guard() -> None:
    src = mod.compose(_drift())
    assert "frappe.db.exists('Property Setter', 'Sales Order-naming_series-options')" in src


def test_compose_emits_property_setter_doc() -> None:
    src = mod.compose(_drift())
    assert '"doctype": "Property Setter"' in src
    assert '"property": "naming_series"' in src


if __name__ == "__main__":
    test_matches_property_setter()
    test_does_not_match_other_doctype()
    test_compose_emits_valid_python()
    test_compose_uses_doctype_name_guard()
    test_compose_emits_property_setter_doc()
    print("OK test__v14_compose_property_setter")
