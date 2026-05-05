"""Rule 3 — JSON top-level property-modification → Property Setter fixture rows.

Handles real Property Setter targets (e.g. `naming_rule`, `default_print_format`).
Additions to the `fields` array are NOT handled here — they are routed by
`core_diff_added_field` to Custom Field fixtures (#347).
"""
from __future__ import annotations
from tools.customisation_audit import core_diff_canonical, core_diff_objects
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "in_place_core_edit"


def _additions(bc: dict, ac: dict) -> list[tuple[str, object]]:
    """Top-level prop additions; excludes fields[X] (→ core_diff_added_field, #347)."""
    return [(k, ac[k]) for k in sorted(set(ac) - set(bc) - {"permissions", "fields"})]


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
    pairs = _additions(bc, ac)
    if not pairs:
        return None
    parent, name = a.get("name", ""), f"{app}/{rel_path}"
    return [Drift(
        id=stable_id(DRIFT_CLASS, name, "prop", k),
        drift_class=DRIFT_CLASS,
        verdict=Verdict.FIXTURE_EQUIVALENT_CORE_EDIT.value,
        doctype="Property Setter", name=f"{name}#{k}",
        owning_app_proposed="", fixture_path_proposed="",
        promotion_strategy=PromotionStrategy.FIXTURE_JSON.value,
        row_data={"doctype_or_field": "DocType", "doc_type": parent,
                  "property": k, "value": v},
        diff=diff,
    ) for k, v in pairs]
