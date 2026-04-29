"""Class 5.4 — Client Script. DB scan vs <app>/fixtures/custom_scripts/<DocType>.js."""

from __future__ import annotations

from tools.customisation_audit import app_inventory, db_query, target_resolution
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "client_script"
DOCTYPE = "Client Script"
SQL = "SELECT name, dt, view, script, enabled FROM `tabClient Script`"
# v13 has no `module` column on tabClient Script.


def _file_exists_for(apps: list[str], dt: str) -> str | None:
    """Return owning app if <app>/<app>/fixtures/custom_scripts/<dt>.js exists, else None."""
    for app in apps:
        path = app_inventory.app_dir(app) / app / "fixtures" / "custom_scripts" / f"{dt}.js"
        if path.exists():
            return app
    return None


def run(config: AuditConfig) -> list[Drift]:
    rows = db_query.run_query(config.ssh_host, config.site_config_path, SQL)
    mapping = target_resolution.module_to_app(config.bespoke_apps)
    drifts: list[Drift] = []
    for row in rows:
        if _file_exists_for(config.bespoke_apps, row.get("dt", "")):
            continue
        owning = target_resolution.resolve_owning_app(row.get("module", ""), mapping)
        proposed = (
            f"{owning}/{owning}/fixtures/custom_scripts/{row.get('dt', '')}.js"
            if owning else ""
        )
        drifts.append(Drift(
            id=stable_id(DRIFT_CLASS, row["name"], row.get("dt", "")),
            drift_class=DRIFT_CLASS, verdict=Verdict.DB_ONLY.value,
            doctype=row.get("dt", ""), name=row["name"], owning_app_proposed=owning,
            fixture_path_proposed=proposed,
            promotion_strategy=(PromotionStrategy.FIXTURES_CUSTOM_SCRIPTS if owning
                                else PromotionStrategy.MANUAL).value,
            row_data=row,
        ))
    return drifts
