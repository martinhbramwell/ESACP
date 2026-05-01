"""Promote `fixtures_custom_scripts` drifts — write `<DocType>.js` script body.

Target: `<app>/<app>/fixtures/custom_scripts/<DocType>.js`. Phase 1 emits a
relative path in `fixture_path_proposed`; promote_common prepends BESPOKE_ROOT.
"""

from __future__ import annotations

from pathlib import Path

from tools.customisation_audit import promote_common


def _get(drift: dict | object, key: str):
    if isinstance(drift, dict):
        return drift.get(key, "")
    return getattr(drift, key, "")


def target(drift: dict | object) -> Path:
    owning = promote_common.resolve_owning(drift)
    dt = (_get(drift, "row_data") or {}).get("dt", "")
    fallback = promote_common.app_pkg_root(owning) / "fixtures" / "custom_scripts" / f"{dt}.js"
    return promote_common.resolve_path(drift, fallback)


def compose(drift: dict | object) -> str:
    """The JS body — Frappe Client Script payload — with trailing newline."""
    body = (_get(drift, "row_data") or {}).get("script", "") or ""
    return body if body.endswith("\n") else body + "\n"


def apply(drift: dict | object) -> Path:
    path = target(drift)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(compose(drift))
    return path
