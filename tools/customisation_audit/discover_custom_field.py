"""Class 5.1 — Custom Field. DB scan vs all bespoke apps' custom_field.json."""

from __future__ import annotations

from tools.customisation_audit import app_inventory, db_query, drift_builder, target_resolution
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift
from tools.customisation_audit.verdict import PromotionStrategy

DRIFT_CLASS = "custom_field"
DOCTYPE = "Custom Field"
KEY_FIELDS = ("dt", "fieldname")
SQL = (
    "SELECT name, dt, fieldname, label, fieldtype, options "
    "FROM `tabCustom Field`"
)
# Note: v13 tabCustom Field has no `module` column. Owning-app attribution
# for db_only entries falls back to "" (manual promotion); fixture-indexed
# entries derive ownership from which app's custom_field.json contains them.


def _index_fixtures(apps: list[str]) -> dict[str, tuple[str, dict]]:
    """name → (owning_app, fixture_row) across every app's custom_field.json."""
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
