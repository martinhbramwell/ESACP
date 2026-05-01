"""Rule 1 — translation CSV under */translations/*.csv."""

from __future__ import annotations

from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "in_place_core_edit"


def matches(rel_path: str) -> bool:
    return rel_path.endswith(".csv") and "/translations/" in rel_path.replace("\\", "/")


def classify(app: str, rel_path: str, diff: str,
             before: str, after: str) -> list[Drift] | None:
    if not matches(rel_path):
        return None
    name = f"{app}/{rel_path}"
    return [Drift(
        id=stable_id(DRIFT_CLASS, name, "translation"),
        drift_class=DRIFT_CLASS,
        verdict=Verdict.FIXTURE_EQUIVALENT_CORE_EDIT.value,
        doctype="(translation_csv)",
        name=name,
        owning_app_proposed="",
        fixture_path_proposed="",
        promotion_strategy=PromotionStrategy.APP_TRANSLATIONS_CSV.value,
        row_data={"app": app, "path": rel_path},
        diff=diff,
        notes=["app_translations_csv"],
    )]
