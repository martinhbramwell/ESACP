#!/usr/bin/env python3
"""Tests for attribution — load, lookup, append_stubs, stub_unmapped_from_report."""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import attribution  # noqa: E402

_RESOLVED = {"owning_app": "ce_sri", "promotion_strategy": "fixture_json"}
_TODO_OWNING = {"owning_app": "TODO", "promotion_strategy": "fixture_json"}


def test_lookup_resolved_entry() -> None:
    assert attribution.lookup({"custom_field": {"X": _RESOLVED}}, "custom_field", "X") == _RESOLVED


def test_lookup_todo_returns_none() -> None:
    assert attribution.lookup({"custom_field": {"X": _TODO_OWNING}}, "custom_field", "X") is None
    assert attribution.lookup({}, "custom_field", "X") is None
    assert attribution.lookup({"custom_field": {}}, "custom_field", "X") is None


def test_append_stubs_only_adds_new() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "attr.yml"
        assert attribution.append_stubs(path, "custom_field", ["A", "B"]) == 2
        assert attribution.append_stubs(path, "custom_field", ["A", "C"]) == 1


def test_stub_unmapped_picks_only_unmapped() -> None:
    rpt = {"drifts": [
        {"class": "custom_field", "name": "X", "promotion_strategy": "manual", "owning_app_proposed": ""},
        {"class": "custom_field", "name": "Y", "promotion_strategy": "fixture_json", "owning_app_proposed": "ce_sri"},
        {"class": "workflow", "name": "Z", "promotion_strategy": "manual", "owning_app_proposed": ""},
    ]}
    with tempfile.TemporaryDirectory() as td:
        assert attribution.stub_unmapped_from_report(Path(td) / "x.yml", rpt) == {"custom_field": 1, "workflow": 1}


_RULE = {"class": "custom_field", "when": {"dt_in": ["Sales Order"]},
         "then": {"owning_app": "ce_sri", "promotion_strategy": "fixture_json"}}


def test_resolve_per_name_wins_over_rule() -> None:
    amap = {"custom_field": {"X": _RESOLVED}, "auto_rules": [_RULE]}
    assert attribution.resolve(amap, "custom_field", "X", {"dt": "Sales Order"}) == _RESOLVED


def test_resolve_todo_falls_through_to_rule() -> None:
    amap = {"custom_field": {"X": _TODO_OWNING}, "auto_rules": [_RULE]}
    out = attribution.resolve(amap, "custom_field", "X", {"dt": "Sales Order"})
    assert out == _RULE["then"]


def test_resolve_no_match_returns_none() -> None:
    amap = {"auto_rules": [_RULE]}
    assert attribution.resolve(amap, "custom_field", "X", {"dt": "Item"}) is None


def test_resolve_rule_match_when_no_per_name_entry() -> None:
    amap = {"auto_rules": [_RULE]}
    assert attribution.resolve(amap, "custom_field", "X", {"dt": "Sales Order"}) == _RULE["then"]


if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_") and callable(fn):
            fn()
    print("OK test_attribution")
