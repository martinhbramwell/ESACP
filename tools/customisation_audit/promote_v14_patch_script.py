"""Promote `v14_patch_script` drifts — render runtime Frappe-doc-insert patch.

Q5 (locked design): fixture-tested only in Phase 2; real-data acceptance
folds into Phase 5. Each patch creates a Frappe doc at `bench migrate` time
from `row_data`, idempotent via `frappe.db.exists` check on the row's `name`.
Patch is registered in `<app>/<app>/patches.txt` so bench picks it up.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.customisation_audit import promote_common


def _get(drift, key):
    if isinstance(drift, dict):
        return drift.get(key, "")
    return getattr(drift, key, "")


def patch_module_name(drift) -> str:
    """Stable module-safe name from drift.name (last path segment, snake-cased)."""
    raw = _get(drift, "name").split("#")[0].split("/")[-1]
    return promote_common.snake(raw) or "patch"


def target(drift) -> Path:
    owning = promote_common.resolve_owning(drift)
    return (promote_common.app_pkg_root(owning) / "patches" / "v14_0"
            / f"{patch_module_name(drift)}.py")


def patches_txt_entry(drift) -> str:
    owning = promote_common.resolve_owning(drift)
    return f"{owning}.patches.v14_0.{patch_module_name(drift)}"


def compose(drift) -> str:
    """Frappe-doc-insert patch script with idempotent existence guard."""
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


def apply(drift) -> Path:
    path = target(drift)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(compose(drift))
    pt = path.parent.parent.parent / "patches.txt"
    entry = patches_txt_entry(drift)
    existing = pt.read_text() if pt.exists() else ""
    if entry not in existing.splitlines():
        sep = "" if not existing or existing.endswith("\n") else "\n"
        pt.write_text(existing + sep + entry + "\n")
    return path
