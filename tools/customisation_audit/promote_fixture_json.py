"""Promote `fixture_json` drifts — upsert row into `<app>/<app>/fixtures/<doctype>.json`.

Match key is `name`. row_data is written verbatim plus a `doctype` field.
Path resolves via Phase 1's `fixture_path_proposed` (absolute or relative);
falls back to `<owning>/<owning>/fixtures/<snake_doctype>.json` for Phase 4
in_place_core_edit drifts that don't pre-compute a path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.customisation_audit import promote_common


def _get(drift: dict | object, key: str) -> Any:
    return drift[key] if isinstance(drift, dict) else getattr(drift, key)


def target(drift: dict | object) -> Path:
    owning = promote_common.resolve_owning(drift)
    fallback = (promote_common.app_pkg_root(owning) / "fixtures"
                / f"{promote_common.snake(_get(drift, 'doctype'))}.json")
    return promote_common.resolve_path(drift, fallback)


def compose(drift: dict | object) -> str:
    """Build proposed full-file JSON text. Pure — does not touch disk except read."""
    path = target(drift)
    existing: list[dict[str, Any]] = (
        json.loads(path.read_text()) if path.exists() else []
    )
    new_row = dict(_get(drift, "row_data"))
    new_row.setdefault("doctype", _get(drift, "doctype"))
    new_row.setdefault("name", _derive_name(new_row))
    name = new_row["name"]
    merged = [r for r in existing if r.get("name") != name] + [new_row]
    return json.dumps(merged, indent=1, sort_keys=True) + "\n"


def _derive_name(row: dict) -> str:
    """Synthesise Frappe doc `name` for rows that don't carry one.

    Property Setter: `<doc_type>-<property>` (matches Frappe autoname).
    Fallback: empty string (caller passes through).
    """
    if row.get("doctype") == "Property Setter":
        return f"{row.get('doc_type', '')}-{row.get('property', '')}"
    return row.get("name", "")


def apply(drift: dict | object) -> Path:
    path = target(drift)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(compose(drift))
    return path
