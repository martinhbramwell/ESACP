"""Rules 6 + 7 — non-JSON files and unrecognised JSON shapes."""
from __future__ import annotations

from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "in_place_core_edit"


def classify(app: str, rel_path: str, diff: str,
             before: str, after: str) -> list[Drift] | None:
    is_json = rel_path.endswith(".json")
    note = "non-JSON" if not is_json else "JSON shape unrecognised"
    name = f"{app}/{rel_path}"
    return [Drift(
        id=stable_id(DRIFT_CLASS, name, "human"),
        drift_class=DRIFT_CLASS,
        verdict=Verdict.HUMAN_REVIEW_CORE_EDIT.value,
        doctype="(human_review)",
        name=name,
        owning_app_proposed="",
        fixture_path_proposed="",
        promotion_strategy=PromotionStrategy.MANUAL.value,
        diff=diff,
        notes=[note],
    )]
