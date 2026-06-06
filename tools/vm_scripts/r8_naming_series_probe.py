#!/usr/bin/env python3
"""r8_naming_series_probe.py — End-to-end naming-series acceptance probe.

V13->V16 post-migrate probe R8 (ESACP#617, #480 child). V16 renamed only the
Naming Series ADMIN surface (Naming Series DocType -> Document Naming Settings);
the autoname mechanism is unchanged. This probe proves it end-to-end: it
creates a real draft Sales Invoice on the test series for the designated test
customer + item, and asserts the new document name == the incremented series
value. Probe-only (no fix); V13-safe (same frappe autoname API on both majors).

Idempotent verdict: each run advances the test series by exactly one and leaves
one draft invoice as evidence; the assertion (name == prefix+(current+1)) is
deterministic regardless of run count. The default company is read at runtime
(never hardcoded) so no tenant identity is baked into this committed script.
"""
import argparse
from pathlib import Path

import frappe

SERIES = "001-004-.#########"      # tenant test naming-series (Sales Invoice)
SERIES_PREFIX = "001-004-"
SERIES_DIGITS = 9
TEST_CUSTOMER = "Compruebalo"       # purpose-built naming-probe fixtures
TEST_ITEM = "Item de Prueba"


def expected_name(prefix, current, digits):
    return f"{prefix}{str(current + 1).zfill(digits)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--bench-dir", required=True)
    args = ap.parse_args()

    frappe.init(site=args.site, sites_path=str(Path(args.bench_dir) / "sites"))
    frappe.connect()

    current = frappe.db.sql(
        "SELECT current FROM tabSeries WHERE name = %s", (SERIES_PREFIX,)
    )
    c0 = current[0][0] if current else 0
    want = expected_name(SERIES_PREFIX, c0, SERIES_DIGITS)

    company = frappe.db.get_single_value("Global Defaults", "default_company")
    doc = frappe.get_doc({
        "doctype": "Sales Invoice",
        "naming_series": SERIES,
        "company": company,
        "customer": TEST_CUSTOMER,
        "posting_date": frappe.utils.nowdate(),
        "due_date": frappe.utils.nowdate(),
        "set_posting_time": 1,
        "items": [{"item_code": TEST_ITEM, "qty": 1, "rate": 1}],
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    if doc.name != want:
        print(f"  [FAIL] series mismatch: got '{doc.name}' expected '{want}' "
              f"(was {SERIES_PREFIX}{str(c0).zfill(SERIES_DIGITS)})")
        print("  [PROBE] naming_series=mismatch")
        frappe.destroy()
        return

    print(f"  [OK] Sales Invoice '{doc.name}' (series advanced) "
          f"customer='{TEST_CUSTOMER}' item='{TEST_ITEM}'")
    print("  [PROBE] naming_series=ok")
    frappe.destroy()


if __name__ == "__main__":
    main()
