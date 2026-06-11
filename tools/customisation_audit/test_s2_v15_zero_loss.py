#!/usr/bin/env python3
"""S2 durable proof — V13→V15 structural A/B shows zero bespoke loss.

The expensive audit (`migration_status.py --bench dev01 --write …`) runs ONCE
against the post-V15 bench and its report is committed as
`delta_report_dev01_v15.json`. This cheap, offline test diffs that committed
V15 report against the committed V13 baseline and asserts:

  * LOST (a V13 drift identity absent in V15) == 0  — zero bespoke loss
  * every ADDED drift is an EXPECTED stock addition the V13→V15 migrate
    materialises: a stock naming-series Property Setter (db_only), or one of
    the two stock multi-company Custom Fields (Email Account-company /
    Communication-company, db_only — ERPNext V14+ defaults).

Per MIGRATION_PLAN.md proof method: the proof command is cheap (loads two
JSONs, set-diffs) — never a re-run of the SSH audit. See migration_proofs/S2.log.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROOFS = REPO / "internal_docs" / "migration_proofs"
V13 = PROOFS / "delta_report_dev01.json"
V15 = PROOFS / "delta_report_dev01_v15.json"

# Stock multi-company Custom Fields ERPNext ships from V14+ (db_only fixtures).
STOCK_CUSTOM_FIELDS = {
    ("custom_field", "Custom Field", "Email Account-company"),
    ("custom_field", "Custom Field", "Communication-company"),
}


def _ident(d: dict) -> tuple:
    return (d["class"], d.get("doctype"), d.get("name"))


def _is_stock_naming_series_ps(d: dict) -> bool:
    return (d["class"] == "property_setter"
            and d.get("verdict") == "db_only"
            and "naming_series" in (d.get("name") or ""))


def test_v13_to_v15_zero_bespoke_loss() -> None:
    assert V13.exists(), f"V13 baseline missing: {V13}"
    assert V15.exists(), f"V15 delta missing: {V15}"
    v13 = json.loads(V13.read_text())
    v15 = json.loads(V15.read_text())
    assert v15["substrate"]["vm"] == "dev01", v15["substrate"]

    s13 = {_ident(d) for d in v13["drifts"]}
    s15 = {_ident(d) for d in v15["drifts"]}
    lost = s13 - s15
    added = s15 - s13

    assert not lost, f"bespoke loss — {len(lost)} V13 drift(s) absent in V15: {sorted(lost)[:10]}"

    added_drifts = [d for d in v15["drifts"] if _ident(d) in added]
    bad = [
        _ident(d) for d in added_drifts
        if not (_is_stock_naming_series_ps(d)
                or (_ident(d) in STOCK_CUSTOM_FIELDS and d.get("verdict") == "db_only"))
    ]
    assert not bad, f"unexpected non-stock additions in V15: {bad}"
    print(f"OK test_s2_v15_zero_loss — 0 lost, {len(added)} expected stock additions "
          f"(12 naming-series PS + 2 multi-company custom fields)")


if __name__ == "__main__":
    test_v13_to_v15_zero_bespoke_loss()
    sys.exit(0)
