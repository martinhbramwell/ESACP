"""Apply operator-curated attribution to Phase 4 in_place_core_edit drifts (#327).

Phase 4 emits drifts with empty `owning_app_proposed` because the JSON-rule
classifier has no app-affinity context. Operators resolve attribution via
`./tools/review_attribution.py`, persisted in
`config/customisation_attribution.yml`. This module overlays those choices
onto Drift objects so Phase 2 promotion routes correctly without modifying
the per-rule classifiers.
"""

from __future__ import annotations

import dataclasses

from tools.customisation_audit import attribution
from tools.customisation_audit.drift import Drift


def apply_attribution(drifts: list[Drift], amap: dict) -> list[Drift]:
    """Override owning_app + strategy from attribution map; pass through if no entry."""
    return [_one(d, amap) for d in drifts]


def _one(drift: Drift, amap: dict) -> Drift:
    entry = attribution.lookup(amap, drift.drift_class, drift.name)
    if not entry:
        return drift
    return dataclasses.replace(
        drift,
        owning_app_proposed=entry["owning_app"],
        promotion_strategy=entry["promotion_strategy"],
    )
