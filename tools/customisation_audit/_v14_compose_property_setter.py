"""Compose a generic Property Setter (or fallback) patch.

Default fallback for v14_patch_script drifts that don't match a more
specific shape. Keys idempotency on (doctype, name) since Property Setter
`name` is the unique key. Used for top-level Property Setter changes (real
properties like `naming_rule`, NOT `fields[X]` additions — those route to
`_v14_compose_custom_field.py`).
"""

from __future__ import annotations

import json

from tools.customisation_audit.promote_common import _get


def matches(drift) -> bool:
    return _get(drift, "doctype") == "Property Setter"


def compose(drift) -> str:
    doctype = _get(drift, "doctype")
    row = dict(_get(drift, "row_data") or {})
    row.setdefault("doctype", doctype)
    name = row.get("name") or ""
    return (f'"""V14 patch — auto-generated for {doctype} / {_get(drift, "name")}."""\n\n'
            "import frappe\n\n\n"
            "def execute():\n"
            f"    if {name!r} and frappe.db.exists({doctype!r}, {name!r}):\n"
            "        return\n"
            f"    frappe.get_doc({json.dumps(row, sort_keys=True, indent=4)}).insert(ignore_permissions=True)\n"
            "    frappe.db.commit()\n")
