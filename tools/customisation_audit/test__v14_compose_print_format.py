#!/usr/bin/env python3
"""Tests for _v14_compose_print_format — DB-side Print Format rows."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import _v14_compose_print_format as mod  # noqa: E402


def _drift() -> dict:
    """Real audit shape: doctype is the parent DocType, class identifies the row type."""
    return {
        "class": "print_format",
        "doctype": "Sales Order",
        "name": "PF: O. de V. 2",
        "row_data": {
            "name": "PF: O. de V. 2", "doc_type": "Sales Order",
            "module": "Selling", "standard": "No", "disabled": 0,
        },
    }


def test_matches_print_format_via_class_key() -> None:
    assert mod.matches(_drift()) is True


def test_matches_print_format_via_drift_class_key() -> None:
    """Drift dataclass / fixture shape uses `drift_class`; both must match."""
    d = _drift()
    d["drift_class"] = d.pop("class")
    assert mod.matches(d) is True


def test_does_not_match_other_class() -> None:
    d = _drift()
    d["class"] = "translation"
    assert mod.matches(d) is False


def test_compose_emits_valid_python() -> None:
    ast.parse(mod.compose(_drift()))


def test_compose_uses_name_idempotency_guard() -> None:
    src = mod.compose(_drift())
    assert "frappe.db.exists('Print Format', 'PF: O. de V. 2')" in src


def test_compose_emits_print_format_doc() -> None:
    src = mod.compose(_drift())
    assert '"doctype": "Print Format"' in src
    assert '"doc_type": "Sales Order"' in src
    assert '"module": "Selling"' in src


if __name__ == "__main__":
    test_matches_print_format_via_class_key()
    test_matches_print_format_via_drift_class_key()
    test_does_not_match_other_class()
    test_compose_emits_valid_python()
    test_compose_uses_name_idempotency_guard()
    test_compose_emits_print_format_doc()
    print("OK test__v14_compose_print_format")
