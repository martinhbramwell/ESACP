"""Rule 4 — JSON modifications that lose no business state when discarded.

Fires when neither permissions, fields, nor non-canonical top-level keys
have additions in `after` vs `before` (canonicalized; deletion-dominant
reformats also count as discardable).
"""
from __future__ import annotations

from tools.customisation_audit import core_diff_canonical, core_diff_objects
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "in_place_core_edit"


def classify(app: str, rel_path: str, diff: str,
             before: str, after: str) -> list[Drift] | None:
    if not rel_path.endswith(".json"):
        return None
    b, a = core_diff_objects.load_pair(before, after)
    if b is None or a is None:
        return None
    bc = core_diff_canonical.canonicalize(b)
    ac = core_diff_canonical.canonicalize(a)
    if core_diff_canonical.has_new_business(bc, ac, diff):
        return None
    name = f"{app}/{rel_path}"
    return [Drift(
        id=stable_id(DRIFT_CLASS, name, "discardable"),
        drift_class=DRIFT_CLASS,
        verdict=Verdict.DISCARDABLE_CORE_EDIT.value,
        doctype="(core_json)",
        name=name,
        owning_app_proposed="",
        fixture_path_proposed="",
        promotion_strategy=PromotionStrategy.NONE.value,
        diff=diff,
        notes=["no new business state"],
    )]
