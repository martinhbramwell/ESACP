#!/usr/bin/env python3
"""Tests for core_diff_property — top-level property changes only.

`fields[X]` additions are no longer handled here (#347) — they are emitted
by `core_diff_added_field` as Custom Field drifts. This test now asserts
the negative: address.json's only post-canonicalize change is field
additions, so core_diff_property must return None.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import core_diff_property as mod  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures_core_edits"


def test_address_json_no_top_level_prop_additions_returns_none() -> None:
    """address.diff only adds fields (barrio, delivery_route); no new top-level props.

    `fields[X]` is intentionally excluded from `_additions()` so it falls
    through to `core_diff_added_field`. With nothing for this rule to emit,
    classify must return None.
    """
    diff = (FIX / "address.diff").read_text()
    before = (FIX / "address_before.json").read_text()
    after = (FIX / "address_after.json").read_text()
    out = mod.classify("frappe", "frappe/contacts/doctype/address/address.json",
                       diff, before, after)
    assert out is None, f"expected None for fields-only diff; got {out!r}"


def test_party_type_no_business_returns_none() -> None:
    diff = (FIX / "party_type.diff").read_text()
    before = (FIX / "party_type_before.json").read_text()
    after = (FIX / "party_type_after.json").read_text()
    out = mod.classify("erpnext", "erpnext/setup/doctype/party_type/party_type.json",
                       diff, before, after)
    assert out is None


if __name__ == "__main__":
    test_address_json_no_top_level_prop_additions_returns_none()
    test_party_type_no_business_returns_none()
    print("OK test_core_diff_property")
