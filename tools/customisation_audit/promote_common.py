"""Shared helpers for promote_*.py modules — path resolution + skip rules."""

from __future__ import annotations

import re
from pathlib import Path

from tools.bespoke_root import BESPOKE_ROOT

DEFAULT_OWNING_APP = "ce_sri"
NON_BESPOKE_OWNERS = {"in_core", "not_ours", ""}  # skip — not a writable bespoke app


def snake(s: str) -> str:
    """'Custom Field' → 'custom_field'; 'FdI: Cotización' → 'fdi_cotizaci_n'.

    ASCII-only — Python module names (used by patches.txt) cannot contain
    non-ASCII characters.
    """
    return re.sub(r"\W+", "_", s, flags=re.ASCII).strip("_").lower()


def resolve_owning(drift: dict | object) -> str:
    """Operator attribution wins; fallback to DEFAULT_OWNING_APP for empty."""
    owning = _get(drift, "owning_app_proposed")
    return owning or DEFAULT_OWNING_APP


def app_pkg_root(owning_app: str) -> Path:
    """`<BESPOKE_ROOT>/<app>/<app>` — Frappe app package root."""
    return BESPOKE_ROOT / owning_app / owning_app


def is_bespoke_writable(drift: dict | object) -> bool:
    """False if the drift's owner is not a writable bespoke app (in_core/not_ours)."""
    return _get(drift, "owning_app_proposed") not in NON_BESPOKE_OWNERS


def resolve_path(drift: dict | object, fallback: Path) -> Path:
    """Use drift.fixture_path_proposed if absolute; if relative, prepend BESPOKE_ROOT.

    Falls back to `fallback` when fixture_path_proposed is empty (Phase 4 case).
    """
    raw = _get(drift, "fixture_path_proposed") or ""
    if not raw:
        return fallback
    p = Path(raw)
    return p if p.is_absolute() else BESPOKE_ROOT / p


def _get(drift, key):
    if isinstance(drift, dict):
        return drift.get(key, "")
    return getattr(drift, key, "")
