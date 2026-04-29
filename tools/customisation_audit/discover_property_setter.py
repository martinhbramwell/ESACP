"""Class 5.2 — Property Setter. DB scan vs ce_sri's property_setter.json."""

from __future__ import annotations

from tools.customisation_audit import app_inventory, db_query, drift_builder, target_resolution
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift
from tools.customisation_audit.verdict import PromotionStrategy

DRIFT_CLASS = "property_setter"
DOCTYPE = "Property Setter"
KEY_FIELDS = ("doc_type", "field_name", "property")
SQL = (
    "SELECT name, doc_type, field_name, property, value, property_type "
    "FROM `tabProperty Setter`"
)  # v13 has no `module` column on tabProperty Setter.


def _index_fixtures(apps: list[str]) -> dict[str, tuple[str, dict]]:
    out: dict[str, tuple[str, dict]] = {}
    for app in apps:
        for entry in app_inventory.load_fixture_file(app, DOCTYPE):
            out[entry["name"]] = (app, entry)
    return out


def run(config: AuditConfig) -> list[Drift]:
    rows = db_query.run_query(config.ssh_host, config.site_config_path, SQL)
    fixtures = _index_fixtures(config.bespoke_apps)
    mapping = target_resolution.module_to_app(config.bespoke_apps)
    seen = {r["name"] for r in rows}
    drifts = [
        drift_builder.db_only(DRIFT_CLASS, DOCTYPE, r, KEY_FIELDS, mapping,
                              PromotionStrategy.FIXTURE_JSON)
        for r in rows if r["name"] not in fixtures
    ]
    drifts += [
        drift_builder.orphan_fixture(DRIFT_CLASS, DOCTYPE, n, a, e, KEY_FIELDS)
        for n, (a, e) in fixtures.items() if n not in seen
    ]
    return drifts
