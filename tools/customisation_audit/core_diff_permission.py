"""Rule 2 — JSON permission-array additions → Custom DocPerm fixture rows."""
from __future__ import annotations
from tools.customisation_audit import core_diff_objects
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "in_place_core_edit"
_ACTIONS = {"read", "write", "create", "delete", "submit", "cancel", "amend",
            "report", "export", "import", "set_user_permissions", "share",
            "print", "email", "select"}


def _is_permission(obj: dict) -> bool:
    return "role" in obj and any(k in obj for k in _ACTIONS)


def classify(app: str, rel_path: str, diff: str,
             before: str, after: str) -> list[Drift] | None:
    if not rel_path.endswith(".json"):
        return None
    perms = []
    for block in core_diff_objects.scan_added_objects(diff):
        obj = core_diff_objects.parse_object(block)
        if obj and _is_permission(obj):
            perms.append(obj)
    if not perms:
        return None
    parent = core_diff_objects.parent_doctype(after)
    name = f"{app}/{rel_path}"
    return [Drift(
        id=stable_id(DRIFT_CLASS, name, "perm", str(i), p.get("role", "")),
        drift_class=DRIFT_CLASS,
        verdict=Verdict.FIXTURE_EQUIVALENT_CORE_EDIT.value,
        doctype="Custom DocPerm", name=f"{name}#{i}",
        owning_app_proposed="", fixture_path_proposed="",
        promotion_strategy=PromotionStrategy.FIXTURE_JSON.value,
        row_data={**p, "parent": parent}, diff=diff,
    ) for i, p in enumerate(perms)]
