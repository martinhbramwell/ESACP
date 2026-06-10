#!/usr/bin/env python3
"""S1 durable proof — V13→V14 structural A/B shows zero bespoke loss.

The expensive audit (`migration_status.py --bench dev01 --write …`) runs ONCE
against the post-V14 bench and its report is committed as
`delta_report_dev01_v14.json`. This cheap, offline test diffs that committed
V14 report against the committed V13 baseline and asserts:

  * LOST (a V13 drift identity absent in V14) == 0  — zero bespoke loss
  * every ADDED drift is a stock naming-series Property Setter — the only
    expected stock addition the V14 migrate materialises (MAT-DT, CRM-LEAD,
    ACC-JV, CUST, … — ERPNext defaults, db_only).

Per MIGRATION_PLAN.md proof method: the proof command is cheap (loads two
JSONs, set-diffs) — never a re-run of the SSH audit. See migration_proofs/S1.log.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROOFS = REPO / "internal_docs" / "migration_proofs"
V13 = PROOFS / "delta_report_dev01.json"
V14 = PROOFS / "delta_report_dev01_v14.json"


def _ident(d: dict) -> tuple:
    return (d["class"], d.get("doctype"), d.get("name"))


def test_v13_to_v14_zero_bespoke_loss() -> None:
    assert V13.exists(), f"V13 baseline missing: {V13}"
    assert V14.exists(), f"V14 delta missing: {V14}"
    v13 = json.loads(V13.read_text())
    v14 = json.loads(V14.read_text())
    assert v14["substrate"]["vm"] == "dev01", v14["substrate"]

    s13 = {_ident(d) for d in v13["drifts"]}
    s14 = {_ident(d) for d in v14["drifts"]}
    lost = s13 - s14
    added = s14 - s13

    assert not lost, f"bespoke loss — {len(lost)} V13 drift(s) absent in V14: {sorted(lost)[:10]}"

    # every addition must be a stock naming-series Property Setter (db_only)
    added_drifts = [d for d in v14["drifts"] if _ident(d) in added]
    bad = [
        _ident(d) for d in added_drifts
        if not (d["class"] == "property_setter"
                and d.get("verdict") == "db_only"
                and "naming_series" in (d.get("name") or ""))
    ]
    assert not bad, f"unexpected non-stock additions in V14: {bad}"
    print(f"OK test_s1_v14_zero_loss — 0 lost, {len(added)} stock property-setter additions")


if __name__ == "__main__":
    test_v13_to_v14_zero_bespoke_loss()
    sys.exit(0)
