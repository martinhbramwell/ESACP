"""Rule 3 — JSON property-modification → Property Setter fixture rows."""
from __future__ import annotations
from tools.customisation_audit import core_diff_canonical, core_diff_objects
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "in_place_core_edit"


def _additions(bc: dict, ac: dict) -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    for k in sorted(set(ac) - set(bc) - {"permissions", "fields"}):
        out.append((k, ac[k]))
    bf = {f.get("fieldname") for f in bc.get("fields", []) if isinstance(f, dict)}
    af = {f.get("fieldname"): f for f in ac.get("fields", []) if isinstance(f, dict)}
    for fn in sorted(set(af) - bf):
        if fn:
            out.append((f"fields[{fn}]", af[fn]))
    return out


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
