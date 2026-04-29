"""Shared Drift constructors used by discover_*.py modules."""

from __future__ import annotations

from tools.customisation_audit import app_inventory, target_resolution
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict


def db_only(drift_class: str, doctype: str, row: dict, key_fields: tuple[str, ...],
            mapping: dict[str, str], strategy: PromotionStrategy,
            attribution_entry: dict | None = None) -> Drift:
    """Build a DB_ONLY drift. Attribution-map entry overrides module-based lookup."""
    if attribution_entry:
        owning = attribution_entry["owning_app"]
        chosen = PromotionStrategy(attribution_entry["promotion_strategy"])
    else:
        owning = target_resolution.resolve_owning_app(row.get("module", ""), mapping)
        chosen = strategy if owning else PromotionStrategy.MANUAL
    fixture_path = str(app_inventory.fixture_path(owning, doctype)) if owning else ""
    return Drift(
        id=stable_id(drift_class, row["name"], *(row.get(k, "") for k in key_fields)),
        drift_class=drift_class, verdict=Verdict.DB_ONLY.value,
        doctype=doctype, name=row["name"], owning_app_proposed=owning,
        fixture_path_proposed=fixture_path,
        promotion_strategy=chosen.value, row_data=row,
    )


def orphan_fixture(drift_class: str, doctype: str, name: str, app: str, entry: dict,
                   key_fields: tuple[str, ...]) -> Drift:
    """Build an ORPHAN_FIXTURE drift entry from a fixture row with no DB match."""
    return Drift(
        id=stable_id(drift_class, name, *(entry.get(k, "") for k in key_fields)),
        drift_class=drift_class, verdict=Verdict.ORPHAN_FIXTURE.value,
        doctype=doctype, name=name, owning_app_proposed=app,
        fixture_path_proposed=str(app_inventory.fixture_path(app, doctype)),
        promotion_strategy=PromotionStrategy.NONE.value, row_data=entry,
    )
