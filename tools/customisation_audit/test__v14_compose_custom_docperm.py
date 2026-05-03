#!/usr/bin/env python3
"""Tests for _v14_compose_custom_docperm — opaque-hash perm shape."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import _v14_compose_custom_docperm as mod  # noqa: E402


def _drift() -> dict:
    return {
        "drift_class": "in_place_core_edit",
        "doctype": "Custom DocPerm",
        "name": "frappe/frappe/core/doctype/user/user.json#7",
        "row_data": {
            "role": "HR Manager", "permlevel": 0, "parent": "User",
            "read": 1, "write": 1, "create": 1, "delete": 1,
        },
    }


def test_matches_custom_docperm() -> None:
    assert mod.matches(_drift()) is True


def test_does_not_match_other_doctype() -> None:
    d = _drift()
    d["doctype"] = "Property Setter"
    assert mod.matches(d) is False


def test_compose_emits_valid_python() -> None:
    ast.parse(mod.compose(_drift()))


def test_compose_uses_parent_role_permlevel_guard() -> None:
    src = mod.compose(_drift())
    assert "frappe.db.exists('Custom DocPerm'" in src
    assert "'parent': 'User'" in src
    assert "'role': 'HR Manager'" in src
    assert "'permlevel': 0" in src


def test_compose_emits_perm_doc() -> None:
    src = mod.compose(_drift())
    assert '"doctype": "Custom DocPerm"' in src
    assert '"role": "HR Manager"' in src
    assert '"parent": "User"' in src


if __name__ == "__main__":
    test_matches_custom_docperm()
    test_does_not_match_other_doctype()
    test_compose_emits_valid_python()
    test_compose_uses_parent_role_permlevel_guard()
    test_compose_emits_perm_doc()
    print("OK test__v14_compose_custom_docperm")
