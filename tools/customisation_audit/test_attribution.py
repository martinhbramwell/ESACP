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


# --- #322 — write-path comment + entry preservation -------------------------

_SEED_YAML = """\
# Operator-curated customisation attribution.
#
# Header comment block — must survive --write-stubs round-trip.
#
#   owning_app:          ce_sri | returnable | route_planner | not_ours
#   promotion_strategy:  fixture_json | fixtures_custom_scripts | manual | none

auto_rules:
  - class: custom_field
    when:
      dt_in: [Sales Order, Customer, Quotation, Sales Invoice, Purchase Invoice, Delivery Note]
    then:
      owning_app: ce_sri
      promotion_strategy: fixture_json

custom_field:
  Customer-compras:
    owning_app: returnable
    promotion_strategy: fixture_json
client_script:
  Delivery Trip-Form:
    owning_app: route_planner
    promotion_strategy: fixtures_custom_scripts
print_format:
  IRS 1099 Form:
    owning_app: not_ours
    promotion_strategy: none
property_setter: {}
"""


def _seed(td: str) -> Path:
    path = Path(td) / "attr.yml"
    path.write_text(_SEED_YAML)
    return path


def test_322_append_stubs_preserves_header_comments() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _seed(td)
        attribution.append_stubs(path, "custom_field", ["NewField"])
        text = path.read_text()
        # Every comment line in the seed must still be present verbatim.
        for line in _SEED_YAML.splitlines():
            if line.startswith("#"):
                assert line in text, f"comment line lost: {line!r}"


def test_322_append_stubs_preserves_existing_entries() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _seed(td)
        attribution.append_stubs(path, "custom_field", ["NewField"])
        amap = attribution.load(path)
        # Existing operator-resolved entries must be intact and lookup-resolvable.
        assert attribution.lookup(amap, "custom_field", "Customer-compras") == {
            "owning_app": "returnable", "promotion_strategy": "fixture_json"
        }
        assert attribution.lookup(amap, "client_script", "Delivery Trip-Form") == {
            "owning_app": "route_planner", "promotion_strategy": "fixtures_custom_scripts"
        }
        assert attribution.lookup(amap, "print_format", "IRS 1099 Form") == {
            "owning_app": "not_ours", "promotion_strategy": "none"
        }


def test_322_append_stubs_adds_new_todo() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _seed(td)
        added = attribution.append_stubs(path, "custom_field", ["Customer-compras", "NewField"])
        assert added == 1  # Customer-compras already exists; only NewField is new
        amap = attribution.load(path)
        assert amap["custom_field"]["NewField"] == {
            "owning_app": "TODO", "promotion_strategy": "TODO"
        }


def test_322_append_stubs_idempotent_when_no_new() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _seed(td)
        # Prime the file by writing once with a new name, capturing the post-write state.
        attribution.append_stubs(path, "custom_field", ["Anchor"])
        before = path.read_text()
        # Second invocation with the same name (already present) must be a no-op rewrite.
        added = attribution.append_stubs(path, "custom_field", ["Anchor"])
        assert added == 0
        assert path.read_text() == before, "no-op rewrite must be byte-identical"


def test_322_no_op_rewrite_is_byte_identical() -> None:
    """Pins long flow-list line preservation — must not line-wrap (regression guard)."""
    with tempfile.TemporaryDirectory() as td:
        path = _seed(td)
        before = path.read_text()
        added = attribution.append_stubs(path, "custom_field", ["Customer-compras"])
        assert added == 0
        assert path.read_text() == before, "no-op rewrite must be byte-identical to seed"


def test_322_append_stubs_preserves_top_level_key_order() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = _seed(td)
        attribution.append_stubs(path, "custom_field", ["NewField"])
        amap = attribution.load(path)
        keys = list(amap.keys())
        # Seed order: auto_rules, custom_field, client_script, print_format, property_setter.
        assert keys == ["auto_rules", "custom_field", "client_script",
                        "print_format", "property_setter"]


if __name__ == "__main__":
    for n, fn in list(globals().items()):
        if n.startswith("test_") and callable(fn):
            fn()
    print("OK test_attribution")
