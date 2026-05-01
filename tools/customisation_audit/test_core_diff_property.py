#!/usr/bin/env python3
"""Tests for core_diff_property — uses real address.json fixture."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import core_diff_property as mod  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures_core_edits"


def test_address_json_emits_property_setter_drifts_for_new_fields() -> None:
    diff = (FIX / "address.diff").read_text()
    before = (FIX / "address_before.json").read_text()
    after = (FIX / "address_after.json").read_text()
    out = mod.classify("frappe", "frappe/contacts/doctype/address/address.json",
                       diff, before, after)
    assert out and len(out) >= 1
    assert all(d.verdict == "fixture_equivalent_core_edit" for d in out)
    assert all(d.promotion_strategy == "fixture_json" for d in out)
    assert all(d.doctype == "Property Setter" for d in out)
    new_fields = {d.row_data.get("property", "") for d in out}
    assert any(fn in {"fields[delivery_route]", "fields[barrio]"} for fn in new_fields)


def test_party_type_no_business_returns_none() -> None:
    diff = (FIX / "party_type.diff").read_text()
    before = (FIX / "party_type_before.json").read_text()
    after = (FIX / "party_type_after.json").read_text()
    out = mod.classify("erpnext", "erpnext/setup/doctype/party_type/party_type.json",
                       diff, before, after)
    assert out is None


if __name__ == "__main__":
    test_address_json_emits_property_setter_drifts_for_new_fields()
    test_party_type_no_business_returns_none()
    print("OK test_core_diff_property")
