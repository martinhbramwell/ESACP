"""Pretty-print drift context for the interactive attribution review CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _substrate_root() -> Path:
    """Resolve the Phase 4 core-tree substrate (production master worktree)."""
    override = os.environ.get("ESACP_CORE_TREE_ROOT")
    if override and Path(override).exists():
        return Path(override)
    default = Path(__file__).resolve().parents[2].parent / "PRODUCTION_20260404" / "apps"
    return default


def _doctype_meta(drift: dict) -> dict | None:
    """Read top-level `module` + `name` from the doctype JSON, if available."""
    src_rel = drift["name"].split("#")[0]
    if not src_rel.endswith(".json"):
        return None
    full = _substrate_root() / src_rel
    try:
        data = json.loads(full.read_text())
        return {"module": data.get("module"), "doctype": data.get("name")}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def summary(drift: dict) -> str:
    cls = drift["class"]
    if cls == "in_place_core_edit":
        return f"{drift['doctype']:<16}  {drift['name']}"
    if cls == "translation":
        rd = drift["row_data"]
        src = (rd.get("source_text") or "")[:40]
        return f"Translation       lang={rd.get('language')!r}  src={src!r}"
    return f"{cls}  {drift['name']}"


def context(drift: dict) -> str:
    cls = drift["class"]
    if cls == "translation":
        return _translation_ctx(drift)
    if cls == "in_place_core_edit":
        return _core_edit_ctx(drift)
    return f"row_data: {drift['row_data']}"


def _translation_ctx(drift: dict) -> str:
    rd = drift["row_data"]
    return ("  ----- DB row -----\n"
            f"  language       : {rd.get('language')!r}\n"
            f"  source_text    : {rd.get('source_text')!r}\n"
            f"  translated_text: {rd.get('translated_text')!r}")


def _core_edit_ctx(drift: dict) -> str:
    diff = drift.get("diff") or ""
    lines = diff.splitlines()
    src = drift["name"].split("#")[0]
    meta = _doctype_meta(drift)
    head = [f"  drift   : {drift['doctype']}"]
    if meta:
        head.append(f"  doctype : {meta['doctype']!r}")
        head.append(f"  module  : {meta['module']!r}")
    head.append(f"  source  : {src}")
    if src.endswith(".json"):
        py_path = src[:-5] + ".py"
        head.append(f"  related : {py_path}  (controller — check for paired Python edits)")
    head += [
        f"  row_data: {drift['row_data']}",
        "",
        "  ----- diff hunk -----",
    ]
    body = ["  " + l for l in lines[:80]]
    if len(lines) > 80:
        body.append(f"  ... ({len(lines) - 80} more lines)")
    return "\n".join(head + body)
