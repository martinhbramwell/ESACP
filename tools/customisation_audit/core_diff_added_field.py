"""Rule 2.5 — additions to a doctype's `fields` array → Custom Field fixture rows.

In-place core edits that add a new entry to the `fields` array of a stock
doctype JSON are conceptually Custom Fields (they extend the doctype with
a new field). They are NOT Property Setter overrides — `fields[X]` is not
a real Frappe property name, and Property Setter records targeting it
crash `bench migrate` because Frappe's importer cannot stringify a nested
dict into a TEXT column cleanly (see #347).

See `_v14_compose_property_setter.py:6-7` for the design distinction:
real properties like `naming_rule` go to property_setter; `fields[X]`
additions belong with custom_field.

This rule runs BEFORE `core_diff_property` so that field additions are
peeled off first; the property rule then handles only true property changes.
"""
from __future__ import annotations

from tools.customisation_audit import core_diff_canonical, core_diff_objects
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "in_place_core_edit"


def _added_fields(bc: dict, ac: dict) -> list[dict]:
    """Field defs present in `after` but not in `before` (matched by fieldname)."""
    bf = {f.get("fieldname") for f in bc.get("fields", []) if isinstance(f, dict)}
    return [
        f for f in ac.get("fields", [])
        if isinstance(f, dict) and f.get("fieldname") and f.get("fieldname") not in bf
    ]


def classify(app: str, rel_path: str, diff: str,
             before: str, after: str) -> list[Drift] | None:
    if not rel_path.endswith(".json"):
        return None
    b, a = core_diff_objects.load_pair(before, after)
    if b is None or a is None:
        return None
    bc = core_diff_canonical.canonicalize(b)
    ac = core_diff_canonical.canonicalize(a)
    if not core_diff_canonical.has_new_business(bc, ac, diff):
        return None
    fields = _added_fields(bc, ac)
    if not fields:
        return None
    parent = a.get("name", "")
    name_base = f"{app}/{rel_path}"
    return [Drift(
        id=stable_id(DRIFT_CLASS, name_base, "field", f["fieldname"]),
        drift_class=DRIFT_CLASS,
        verdict=Verdict.FIXTURE_EQUIVALENT_CORE_EDIT.value,
        doctype="Custom Field",
        name=f"{parent}-{f['fieldname']}",
        owning_app_proposed="",
        fixture_path_proposed="",
        promotion_strategy=PromotionStrategy.FIXTURE_JSON.value,
        row_data={**f, "dt": parent, "name": f"{parent}-{f['fieldname']}"},
        diff=diff,
    ) for f in fields]
