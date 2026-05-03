"""Compose a Custom Field-shaped patch for fields[X]-style in-core edits.

Routed when an `in_place_core_edit` Property Setter drift carries a
`row_data["property"]` like `fields[<fieldname>]`. The fields[] addition is
semantically a Custom Field (per U6 verdict — `(dt, fieldname)` dedupes at
form-render time), so we emit a Custom Field insert rather than a literal
Property Setter, with idempotency keyed on `(dt, fieldname)`.
"""

from __future__ import annotations

import json
import re

from tools.customisation_audit.promote_common import _get, drift_class

_FIELDS_PROP = re.compile(r"^fields\[(?P<fn>[^\]]+)\]$")


def matches(drift) -> bool:
    if drift_class(drift) != "in_place_core_edit":
        return False
    if _get(drift, "doctype") != "Property Setter":
        return False
    row = _get(drift, "row_data") or {}
    return bool(_FIELDS_PROP.match(row.get("property", "") if isinstance(row, dict) else ""))


def compose(drift) -> str:
    row = _get(drift, "row_data") or {}
    dt = row.get("doc_type", "")
    m = _FIELDS_PROP.match(row.get("property", ""))
    fn = m.group("fn") if m else ""
    field_def = dict(row.get("value") or {})
    cf = {"doctype": "Custom Field", "dt": dt, **field_def, "fieldname": fn}
    return (f'"""V14 patch — Custom Field {dt}.{fn} (auto-generated).\n\n'
            f"Drift origin: {_get(drift, 'name')}\n"
            '"""\n\n'
            "import frappe\n\n\n"
            "def execute():\n"
            f"    if frappe.db.exists('Custom Field', {{'dt': {dt!r}, 'fieldname': {fn!r}}}):\n"
            "        return\n"
            f"    frappe.get_doc({json.dumps(cf, sort_keys=True, indent=4)}).insert(ignore_permissions=True)\n"
            "    frappe.db.commit()\n")
