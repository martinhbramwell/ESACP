"""Compose a Print Format patch for DB-resident Print Format drifts.

Discover side: `discover_print_format.py` sets `doctype` to the *parent*
DocType (e.g. Sales Order) — NOT "Print Format" — so the matcher keys on
`drift_class == "print_format"` instead. The compose body always emits
`{"doctype": "Print Format", **row_data}`. Idempotency on `name`.
Generally a no-op once the row exists in the production DB carry-through.
"""

from __future__ import annotations

import json

from tools.customisation_audit.promote_common import _get, drift_class


def matches(drift) -> bool:
    return drift_class(drift) == "print_format"


def compose(drift) -> str:
    row = dict(_get(drift, "row_data") or {})
    name = row.get("name", "")
    doc = {"doctype": "Print Format", **row}
    return (f'"""V14 patch — Print Format {name!r} (auto-generated)."""\n\n'
            "import frappe\n\n\n"
            "def execute():\n"
            f"    if {name!r} and frappe.db.exists('Print Format', {name!r}):\n"
            "        return\n"
            f"    frappe.get_doc({json.dumps(doc, sort_keys=True, indent=4)}).insert(ignore_permissions=True)\n"
            "    frappe.db.commit()\n")
