#!/usr/bin/env python3
"""Tests for promote_fixtures_custom_scripts — write .js to fixtures/custom_scripts/."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["BESPOKE_ROOT"] = "/tmp/test-bespoke-cs"

from tools.customisation_audit import promote_fixtures_custom_scripts as mod  # noqa: E402


def _drift(path: str = "", owning: str = "ce_sri", dt: str = "Address",
           script: str = "frappe.ui.form.on('Address', {refresh: () => {}});") -> dict:
    return {
        "fixture_path_proposed": path,
        "owning_app_proposed": owning,
        "doctype": "Client Script",
        "row_data": {"dt": dt, "name": f"{dt}-Form", "script": script},
    }


def test_target_uses_relative_path_via_bespoke_root() -> None:
    d = _drift(path="ce_sri/ce_sri/fixtures/custom_scripts/Address.js")
    assert mod.target(d) == Path("/tmp/test-bespoke-cs/ce_sri/ce_sri/fixtures/custom_scripts/Address.js")


def test_target_falls_back_to_owning_plus_dt() -> None:
    d = _drift(path="", owning="route_planner", dt="Delivery Trip")
    expected = Path("/tmp/test-bespoke-cs/route_planner/route_planner/fixtures/custom_scripts/Delivery Trip.js")
    assert mod.target(d) == expected


def test_compose_returns_script_body_with_newline() -> None:
    d = _drift(script="alert('hi')")
    assert mod.compose(d) == "alert('hi')\n"


def test_compose_preserves_existing_trailing_newline() -> None:
    d = _drift(script="alert('hi')\n")
    assert mod.compose(d) == "alert('hi')\n"


def test_apply_writes_file_and_creates_parents() -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["BESPOKE_ROOT"] = td
        # Reload module-level constant by re-importing
        import importlib
        import tools.bespoke_root as br
        importlib.reload(br)
        importlib.reload(mod.promote_common)
        importlib.reload(mod)
        d = _drift(path="ce_sri/ce_sri/fixtures/custom_scripts/Address.js",
                   script="alert('promoted')")
        out = mod.apply(d)
        assert out.exists()
        assert out.read_text() == "alert('promoted')\n"
        assert out.parent.is_dir()


if __name__ == "__main__":
    test_target_uses_relative_path_via_bespoke_root()
    test_target_falls_back_to_owning_plus_dt()
    test_compose_returns_script_body_with_newline()
    test_compose_preserves_existing_trailing_newline()
    test_apply_writes_file_and_creates_parents()
    print("OK test_promote_fixtures_custom_scripts")
