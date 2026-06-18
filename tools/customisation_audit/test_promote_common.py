#!/usr/bin/env python3
"""Tests for promote_common — path + owner resolution helpers."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Pin BESPOKE_ROOT before importing the module under test.
os.environ["BESPOKE_ROOT"] = "/tmp/test-bespoke-root"

from tools.customisation_audit import promote_common as mod  # noqa: E402


def test_snake_doctype_to_filename() -> None:
    assert mod.snake("Custom Field") == "custom_field"
    assert mod.snake("Property Setter") == "property_setter"
    assert mod.snake("FdI: Cotización") == "fdi_cotizaci_n"  # ó → _


def test_resolve_owning_uses_operator_value() -> None:
    assert mod.resolve_owning({"owning_app_proposed": "returnable"}) == "returnable"


def test_resolve_owning_falls_back_to_default() -> None:
    assert mod.resolve_owning({"owning_app_proposed": ""}) == "ce_sri"


def test_app_pkg_root() -> None:
    p = mod.app_pkg_root("ce_sri")
    assert p == Path("/tmp/test-bespoke-root/ce_sri/ce_sri")


def test_is_bespoke_writable_true_for_real_app() -> None:
    assert mod.is_bespoke_writable({"owning_app_proposed": "ce_sri"}) is True


def test_is_bespoke_writable_false_for_in_core() -> None:
    assert mod.is_bespoke_writable({"owning_app_proposed": "in_core"}) is False


def test_is_bespoke_writable_false_for_not_ours() -> None:
    assert mod.is_bespoke_writable({"owning_app_proposed": "not_ours"}) is False


def test_is_bespoke_writable_false_for_empty() -> None:
    assert mod.is_bespoke_writable({"owning_app_proposed": ""}) is False


def test_resolve_path_uses_absolute_proposed() -> None:
    drift = {"fixture_path_proposed": "/abs/path/x.json"}
    assert mod.resolve_path(drift, Path("/fallback")) == Path("/abs/path/x.json")


def test_resolve_path_prepends_bespoke_root_for_relative() -> None:
    drift = {"fixture_path_proposed": "ce_sri/ce_sri/fixtures/custom_scripts/Address.js"}
    out = mod.resolve_path(drift, Path("/fallback"))
    assert out == Path("/tmp/test-bespoke-root/ce_sri/ce_sri/fixtures/custom_scripts/Address.js")


def test_resolve_path_falls_back_when_empty() -> None:
    drift = {"fixture_path_proposed": ""}
    fallback = Path("/computed/fallback.json")
    assert mod.resolve_path(drift, fallback) == fallback


if __name__ == "__main__":
    test_snake_doctype_to_filename()
    test_resolve_owning_uses_operator_value()
    test_resolve_owning_falls_back_to_default()
    test_app_pkg_root()
    test_is_bespoke_writable_true_for_real_app()
    test_is_bespoke_writable_false_for_in_core()
    test_is_bespoke_writable_false_for_not_ours()
    test_is_bespoke_writable_false_for_empty()
    test_resolve_path_uses_absolute_proposed()
    test_resolve_path_prepends_bespoke_root_for_relative()
    test_resolve_path_falls_back_when_empty()
    print("OK test_promote_common")
