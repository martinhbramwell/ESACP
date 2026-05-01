"""Priority-ordered rule dispatch — first match wins."""
from __future__ import annotations

from tools.customisation_audit import (
    core_diff_deletion, core_diff_human_review, core_diff_permission,
    core_diff_property, core_diff_translation,
)
from tools.customisation_audit.drift import Drift

# Priority order: translation → permission → property → deletion → human_review fallback.
_RULES = (
    core_diff_translation,
    core_diff_permission,
    core_diff_property,
    core_diff_deletion,
)


def classify(app: str, rel_path: str, diff: str,
             before: str, after: str) -> list[Drift]:
    for rule in _RULES:
        result = rule.classify(app, rel_path, diff, before, after)
        if result:
            return result
    return core_diff_human_review.classify(app, rel_path, diff, before, after) or []
