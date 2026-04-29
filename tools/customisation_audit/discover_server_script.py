"""Class 5.5 — Server Script. Enumerate-only (manual promotion per audit D-5)."""

from __future__ import annotations

from tools.customisation_audit import db_query
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "server_script"
DOCTYPE = "Server Script"
SQL = (
    "SELECT name, script_type, reference_doctype, disabled "
    "FROM `tabServer Script`"
)  # v13 has no `module` column on tabServer Script.


def run(config: AuditConfig) -> list[Drift]:
    rows = db_query.run_query(config.ssh_host, config.site_config_path, SQL)
    return [
        Drift(
            id=stable_id(DRIFT_CLASS, row["name"], row.get("script_type", "")),
            drift_class=DRIFT_CLASS, verdict=Verdict.ENUMERATE_ONLY.value,
            doctype=DOCTYPE, name=row["name"], owning_app_proposed="",
            fixture_path_proposed="",
            promotion_strategy=PromotionStrategy.NONE.value,
            row_data=row, notes=["Server Scripts require manual review per audit D-5."],
        )
        for row in rows
    ]
