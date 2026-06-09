#!/usr/bin/env python3
"""r8_naming_series_probe.py — End-to-end naming-series acceptance probe (R8).

V13->V16 post-migrate probe (ESACP#617, #480 child). V16 renamed only the
Naming Series admin surface; autoname is unchanged. This proves it end-to-end:
creates a real draft Sales Invoice on the tenant test series and asserts the new
name == the incremented series value. Probe-only; V13-safe. Each run advances
the series by exactly one (deterministic regardless of run count); the default
company is read at runtime so no tenant identity is baked into this script.
"""
import argparse
from pathlib import Path

import frappe

SERIES = "001-004-.#########"      # tenant test naming-series (Sales Invoice)
SERIES_PREFIX = "001-004-"
SERIES_DIGITS = 9
TEST_CUSTOMER = "Compruebalo"       # purpose-built naming-probe fixtures
TEST_ITEM = "Item de Prueba"


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
    want = f"{SERIES_PREFIX}{str(c0 + 1).zfill(SERIES_DIGITS)}"

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
