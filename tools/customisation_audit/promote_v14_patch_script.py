"""Promote `v14_patch_script` drifts — shape-aware dispatch to per-shape
compose modules; in_core/empty owners route to the synthetic
`legacy_error_fixes` Frappe app. See Phase 5 plan §4.2.
"""

from __future__ import annotations

from pathlib import Path

from tools.customisation_audit import (
    _v14_compose_custom_docperm,
    _v14_compose_custom_field,
    _v14_compose_print_format,
    _v14_compose_property_setter,
    _v14_compose_translation,
    promote_common,
)
from tools.customisation_audit.promote_common import _get

SYNTHETIC_APP = "legacy_error_fixes"
_NON_BESPOKE_OR_EMPTY = {"in_core", "not_ours", ""}

_DISPATCH = (_v14_compose_custom_field, _v14_compose_custom_docperm,
             _v14_compose_translation, _v14_compose_print_format,
             _v14_compose_property_setter)


def resolve_v14_patch_app(drift) -> str:
    owning = _get(drift, "owning_app_proposed")
    return SYNTHETIC_APP if owning in _NON_BESPOKE_OR_EMPTY else owning


def patch_module_name(drift) -> str:
    """Slug from drift.name; suffix-after-`#` is appended to disambiguate
    multiple drifts on the same source-tree file (e.g. several `fields[X]`
    additions in one JSON). Without this, all collapse to one filename."""
    name = _get(drift, "name")
    base, _, suffix = name.partition("#")
    base_slug = promote_common.snake(base.split("/")[-1])
    if suffix:
        return f"{base_slug}_{promote_common.snake(suffix)}" if base_slug else promote_common.snake(suffix)
    return base_slug or "patch"


def target(drift) -> Path:
    return (promote_common.app_pkg_root(resolve_v14_patch_app(drift))
            / "patches" / "v14_0" / f"{patch_module_name(drift)}.py")


def patches_txt_entry(drift) -> str:
    return f"{resolve_v14_patch_app(drift)}.patches.v14_0.{patch_module_name(drift)}"


def compose(drift) -> str:
    for mod in _DISPATCH:
        if mod.matches(drift):
            return mod.compose(drift)
    return _v14_compose_property_setter.compose(drift)


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
