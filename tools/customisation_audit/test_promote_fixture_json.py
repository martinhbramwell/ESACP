#!/usr/bin/env python3
"""Tests for promote_fixture_json — upsert by name into fixture file."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import promote_fixture_json as mod  # noqa: E402


def _drift(path: Path, name: str, dt: str = "Project", fieldname: str = "x") -> dict:
    return {
        "doctype": "Custom Field",
        "fixture_path_proposed": str(path),
        "row_data": {"name": name, "dt": dt, "fieldname": fieldname,
                     "label": "X", "fieldtype": "Data", "options": None},
    }


def test_compose_creates_new_list_when_path_absent() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "ce_sri" / "ce_sri" / "fixtures" / "custom_field.json"
        text = mod.compose(_drift(path, "Project-x"))
        rows = json.loads(text)
        assert rows == [{
            "doctype": "Custom Field", "name": "Project-x", "dt": "Project",
            "fieldname": "x", "label": "X", "fieldtype": "Data", "options": None,
        }]


def test_compose_appends_when_name_absent() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "custom_field.json"
        path.write_text(json.dumps([{"doctype": "Custom Field", "name": "A-y",
                                     "dt": "A", "fieldname": "y"}]))
        rows = json.loads(mod.compose(_drift(path, "Project-x")))
        assert {r["name"] for r in rows} == {"A-y", "Project-x"}


def test_compose_upserts_when_name_present() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "custom_field.json"
        path.write_text(json.dumps([{"doctype": "Custom Field", "name": "Project-x",
                                     "dt": "Project", "fieldname": "x", "label": "OLD"}]))
        rows = json.loads(mod.compose(_drift(path, "Project-x")))
        assert len(rows) == 1
        assert rows[0]["label"] == "X"  # replaced, not appended


def test_apply_writes_and_creates_parents() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "ce_sri" / "ce_sri" / "fixtures" / "custom_field.json"
        result = mod.apply(_drift(path, "Project-x"))
        assert result == path
        assert path.exists()
        rows = json.loads(path.read_text())
        assert rows[0]["name"] == "Project-x"


def test_compose_round_trip_idempotent() -> None:
    """Applying twice with same drift produces same content."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "custom_field.json"
        d = _drift(path, "Project-x")
        first = mod.compose(d)
        path.write_text(first)
        second = mod.compose(d)
        assert first == second


def test_target_returns_path() -> None:
    assert mod.target({"fixture_path_proposed": "/x/y.json", "row_data": {}, "doctype": ""}) == Path("/x/y.json")


if __name__ == "__main__":
    test_compose_creates_new_list_when_path_absent()
    test_compose_appends_when_name_absent()
    test_compose_upserts_when_name_present()
    test_apply_writes_and_creates_parents()
    test_compose_round_trip_idempotent()
    test_target_returns_path()
    print("OK test_promote_fixture_json")
