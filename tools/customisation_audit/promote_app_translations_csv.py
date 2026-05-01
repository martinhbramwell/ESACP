"""Promote `app_translations_csv` drifts — append CSV row to `<lang>.csv`.

Target: `<app>/<app>/translations/<lang>.csv`. Phase 1 emits empty
`fixture_path_proposed` for translation drifts; we construct from owning_app
and `row_data["language"]`. Idempotent: skips append if source_text already
present in the file.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from tools.customisation_audit import promote_common


def _get(drift: dict | object, key: str):
    if isinstance(drift, dict):
        return drift.get(key, "")
    return getattr(drift, key, "")


def target(drift: dict | object) -> Path:
    owning = promote_common.resolve_owning(drift)
    lang = (_get(drift, "row_data") or {}).get("language") or "en"
    fallback = promote_common.app_pkg_root(owning) / "translations" / f"{lang}.csv"
    return promote_common.resolve_path(drift, fallback)


def compose(drift: dict | object) -> str:
    """Full file content with the new row appended (or unchanged if duplicate)."""
    path = target(drift)
    rd = _get(drift, "row_data") or {}
    src, tx = rd.get("source_text", ""), rd.get("translated_text", "")
    existing = path.read_text() if path.exists() else ""
    for line in existing.splitlines():
        cells = next(csv.reader([line]), [])
        if cells and cells[0] == src:
            return existing if existing.endswith("\n") else existing + "\n"
    buf = io.StringIO()
    csv.writer(buf).writerow([src, tx, ""])
    return existing + ("" if existing.endswith("\n") or not existing else "\n") + buf.getvalue()


def apply(drift: dict | object) -> Path:
    path = target(drift)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(compose(drift))
    return path
