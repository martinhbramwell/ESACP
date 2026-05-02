#!/usr/bin/env python3
"""U6: Frappe (dt, fieldname) dedup smoke test — martinhbramwell/ESACP#335.

SCP to a target VM, run under the bench Python interpreter:

    sudo -u erpadm BENCH/env/bin/python3 u6_dedup_smoke_test.py \\
        --site SITE --bench BENCH

Pass: every probed field has exactly one get_meta entry. Read-only.
"""
import argparse
import json
import os
import sys

PROBES = [
    ("Customer", "forma_de_pago_preferida"),
    ("Address", "barrio"),
    ("Address", "delivery_route"),
    ("Sales Invoice", "comission_entry_created"),
    ("Sales Invoice", "sales_partner_supplier"),
    ("Sales Invoice", "break_down"),
    ("Sales Invoice", "commission_paid"),
    ("Sales Invoice", "forma_de_pago_especificada"),
    ("Sales Order", "data_90"),
    ("Sales Order", "customer_special_note"),
    ("Delivery Note", "saldo_del_cliente"),
    ("Supplier", "purchase_taxes_and_charges_template"),
    ("Purchase Order Item", "comprobante_interno"),
    ("Purchase Order Item", "tipo_comprobante"),
]


def probe(frappe, dt, fieldname):
    cf = frappe.db.sql(
        "SELECT name, fieldtype FROM `tabCustom Field` WHERE dt=%s AND fieldname=%s",
        (dt, fieldname), as_dict=True)
    meta = frappe.get_meta(dt)
    matches = [{"fieldname": f.fieldname, "fieldtype": f.fieldtype, "label": f.label,
                "is_custom_field": bool(getattr(f, "is_custom_field", 0))}
               for f in meta.fields if f.fieldname == fieldname]
    return {"dt": dt, "fieldname": fieldname,
            "tabCustomField_rows": len(cf), "tabCustomField_detail": cf,
            "get_meta_total_fields": len(meta.fields),
            "get_meta_match_count": len(matches), "get_meta_matches": matches}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--site", required=True)
    p.add_argument("--bench", required=True)
    a = p.parse_args()

    os.chdir(os.path.join(a.bench, "sites"))
    import frappe
    frappe.init(site=a.site)
    frappe.connect()
    frappe.clear_cache()

    results = [probe(frappe, dt, fn) for dt, fn in PROBES]
    summary = {"site": a.site, "probes": len(results),
               "passed": all(r["get_meta_match_count"] == 1 for r in results),
               "duplicate_count": sum(1 for r in results if r["get_meta_match_count"] != 1),
               "results": results}
    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
