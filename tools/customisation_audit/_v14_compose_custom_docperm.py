"""Compose a Custom DocPerm patch for permission-row in-core edits.

Custom DocPerm names are opaque hashes (per `customisation_attribution.yml`
comment + #328), so idempotency keys on `(parent, role, permlevel)` rather
than `name`. The `parent` is the DocType the permission applies to.
"""

from __future__ import annotations

import json

from tools.customisation_audit.promote_common import _get, drift_class


def matches(drift) -> bool:
    if drift_class(drift) != "in_place_core_edit":
        return False
    return _get(drift, "doctype") == "Custom DocPerm"


def compose(drift) -> str:
    row = dict(_get(drift, "row_data") or {})
    parent = row.get("parent", "")
    role = row.get("role", "")
    permlevel = row.get("permlevel", 0)
    doc = {"doctype": "Custom DocPerm", **row}
    return (f'"""V14 patch — Custom DocPerm {parent} / {role} / permlevel {permlevel} '
            f"(auto-generated).\n\n"
            f"Drift origin: {_get(drift, 'name')}\n"
            '"""\n\n'
            "import frappe\n\n\n"
            "def execute():\n"
            f"    if frappe.db.exists('Custom DocPerm', "
            f"{{'parent': {parent!r}, 'role': {role!r}, 'permlevel': {permlevel!r}}}):\n"
            "        return\n"
            f"    frappe.get_doc({json.dumps(doc, sort_keys=True, indent=4)}).insert(ignore_permissions=True)\n"
            "    frappe.db.commit()\n")
