"""Class 5.7 — Workflow. DB scan; no fixture mechanism — all rows db_only."""

from __future__ import annotations

from tools.customisation_audit import db_query, target_resolution
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "workflow"
DOCTYPE = "Workflow"
SQL = "SELECT name, document_type, is_active FROM `tabWorkflow`"
# v13 has no `module` column on tabWorkflow.


def run(config: AuditConfig) -> list[Drift]:
    rows = db_query.run_query(config.ssh_host, config.site_config_path, SQL)
    mapping = target_resolution.module_to_app(config.bespoke_apps)
    drifts: list[Drift] = []
    for row in rows:
        owning = target_resolution.resolve_owning_app(row.get("module", ""), mapping)
        drifts.append(Drift(
            id=stable_id(DRIFT_CLASS, row["name"], row.get("document_type", "")),
            drift_class=DRIFT_CLASS, verdict=Verdict.DB_ONLY.value,
            doctype=row.get("document_type", ""), name=row["name"], owning_app_proposed=owning,
            fixture_path_proposed="",
            promotion_strategy=(PromotionStrategy.V14_PATCH_SCRIPT if owning
                                else PromotionStrategy.MANUAL).value,
            row_data=row,
        ))
    return drifts
