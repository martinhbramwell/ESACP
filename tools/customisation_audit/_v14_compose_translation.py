"""Compose a Translation patch for DB-resident Translation drifts.

Discover side: `discover_translation.py` emits row_data with
`(name, language, source_text, translated_text)`. Idempotency keys on
`(language, source_text)` — the natural unique pair for a translation row.
Generally a no-op once the equivalent CSV / DB row already exists in
production (see Phase 5 plan §3 — db-resident "noise" drifts).
"""

from __future__ import annotations

import json

from tools.customisation_audit.promote_common import _get, drift_class


def matches(drift) -> bool:
    return drift_class(drift) == "translation" or _get(drift, "doctype") == "Translation"


def compose(drift) -> str:
    row = dict(_get(drift, "row_data") or {})
    lang = row.get("language", "")
    source = row.get("source_text", "")
    doc = {"doctype": "Translation", **row}
    return (f'"""V14 patch — Translation {lang!r} / {source!r} (auto-generated)."""\n\n'
            "import frappe\n\n\n"
            "def execute():\n"
            f"    if frappe.db.exists('Translation', "
            f"{{'language': {lang!r}, 'source_text': {source!r}}}):\n"
            "        return\n"
            f"    frappe.get_doc({json.dumps(doc, sort_keys=True, indent=4)}).insert(ignore_permissions=True)\n"
            "    frappe.db.commit()\n")
