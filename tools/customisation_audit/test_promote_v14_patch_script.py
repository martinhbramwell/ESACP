#!/usr/bin/env python3
"""Tests for promote_v14_patch_script — Q5 fixture-only acceptance."""

import ast
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["BESPOKE_ROOT"] = "/tmp/test-bespoke-vp"

from tools.customisation_audit import promote_v14_patch_script as mod  # noqa: E402


def _print_format_drift() -> dict:
    return {
        "fixture_path_proposed": "",
        "owning_app_proposed": "ce_sri",
        "doctype": "Print Format",
        "name": "PF: O. de V. 2",
        "row_data": {"name": "PF: O. de V. 2", "doc_type": "Sales Order",
                     "module": "Selling", "standard": "No", "disabled": 0},
    }


def test_patch_module_name_snake_cases() -> None:
    assert mod.patch_module_name(_print_format_drift()) == "pf_o_de_v_2"


def test_patches_txt_entry_format() -> None:
    assert mod.patches_txt_entry(_print_format_drift()) == "ce_sri.patches.v14_0.pf_o_de_v_2"


def test_target_constructs_path() -> None:
    out = mod.target(_print_format_drift())
    assert out == Path("/tmp/test-bespoke-vp/ce_sri/ce_sri/patches/v14_0/pf_o_de_v_2.py")


def test_compose_returns_valid_python() -> None:
    src = mod.compose(_print_format_drift())
    ast.parse(src)  # raises SyntaxError if invalid


def test_compose_includes_frappe_get_doc_with_row() -> None:
    src = mod.compose(_print_format_drift())
    assert "frappe.get_doc(" in src
    assert '"name": "PF: O. de V. 2"' in src
    assert '"doc_type": "Sales Order"' in src
    assert "frappe.db.exists" in src  # idempotency guard


def test_compose_idempotency_guard_uses_doctype_and_name() -> None:
    src = mod.compose(_print_format_drift())
    assert "'Print Format'" in src
    assert "'PF: O. de V. 2'" in src


def test_compose_handles_in_place_property_setter_shape() -> None:
    drift = {
        "fixture_path_proposed": "",
        "owning_app_proposed": "in_core",  # would be skipped by dispatch, but compose still works
        "doctype": "Property Setter",
        "name": "erpnext/erpnext/.../address.json#fields[barrio]",
        "row_data": {"doctype_or_field": "DocType", "doc_type": "Address",
                     "property": "fields[barrio]", "value": {"fieldname": "barrio"}},
    }
    src = mod.compose(drift)
    ast.parse(src)
    assert "Property Setter" in src


def test_apply_writes_patch_and_registers_in_patches_txt() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["BESPOKE_ROOT"] = td
        import importlib
        import tools.bespoke_root as br
        importlib.reload(br)
        importlib.reload(mod.promote_common)
        importlib.reload(mod)
        d = _print_format_drift()
        out = mod.apply(d)
        assert out.exists()
        ast.parse(out.read_text())
        pt = Path(td) / "ce_sri" / "ce_sri" / "patches.txt"
        assert pt.exists()
        assert "ce_sri.patches.v14_0.pf_o_de_v_2" in pt.read_text()


def test_apply_idempotent_on_repeat() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["BESPOKE_ROOT"] = td
        import importlib
        import tools.bespoke_root as br
        importlib.reload(br)
        importlib.reload(mod.promote_common)
        importlib.reload(mod)
        d = _print_format_drift()
        mod.apply(d)
        mod.apply(d)
        pt = Path(td) / "ce_sri" / "ce_sri" / "patches.txt"
        assert pt.read_text().count("ce_sri.patches.v14_0.pf_o_de_v_2") == 1


if __name__ == "__main__":
    test_patch_module_name_snake_cases()
    test_patches_txt_entry_format()
    test_target_constructs_path()
    test_compose_returns_valid_python()
    test_compose_includes_frappe_get_doc_with_row()
    test_compose_idempotency_guard_uses_doctype_and_name()
    test_compose_handles_in_place_property_setter_shape()
    test_apply_writes_patch_and_registers_in_patches_txt()
    test_apply_idempotent_on_repeat()
    print("OK test_promote_v14_patch_script")
