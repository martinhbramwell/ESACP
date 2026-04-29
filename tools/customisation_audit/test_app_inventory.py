#!/usr/bin/env python3
"""Tests for app_inventory — hooks.py parsing + fixture file discovery."""

import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import app_inventory  # noqa: E402
from tools.customisation_audit._test_support import patched  # noqa: E402


def _scaffold(root: Path, name: str, hooks: str, fix: dict[str, list]) -> None:
    inner = root / name / name
    (inner / "fixtures").mkdir(parents=True)
    (inner / "hooks.py").write_text(hooks)
    for fn, content in fix.items():
        (inner / "fixtures" / fn).write_text(json.dumps(content))


def test_parse_fixtures_literal_list() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _scaffold(root, "ce_sri", 'fixtures = ["Custom Field", "Property Setter"]\n', {})
        with patched(app_inventory, "BESPOKE_ROOT", root):
            assert app_inventory.parse_fixtures("ce_sri") == ["Custom Field", "Property Setter"]


def test_parse_fixtures_missing_hooks_returns_empty() -> None:
    with tempfile.TemporaryDirectory() as td:
        with patched(app_inventory, "BESPOKE_ROOT", Path(td)):
            assert app_inventory.parse_fixtures("nonexistent") == []


def test_load_fixture_file_returns_parsed_json() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _scaffold(root, "ce_sri", "fixtures = []\n",
                  {"custom_field.json": [{"name": "X", "dt": "Sales Invoice"}]})
        with patched(app_inventory, "BESPOKE_ROOT", root):
            assert app_inventory.load_fixture_file("ce_sri", "Custom Field") == \
                [{"name": "X", "dt": "Sales Invoice"}]


if __name__ == "__main__":
    test_parse_fixtures_literal_list()
    test_parse_fixtures_missing_hooks_returns_empty()
    test_load_fixture_file_returns_parsed_json()
    print("OK test_app_inventory")
