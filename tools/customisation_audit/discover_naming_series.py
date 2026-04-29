"""Class 5.8 — Naming Series counters. Informational; no promotion required."""

from __future__ import annotations

from tools.customisation_audit import db_query
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "naming_series"
DOCTYPE = "Series"
SQL = "SELECT name, current FROM `tabSeries`"


def run(config: AuditConfig) -> list[Drift]:
    rows = db_query.run_query(config.ssh_host, config.site_config_path, SQL)
    return [
        Drift(
            id=stable_id(DRIFT_CLASS, row["name"]),
            drift_class=DRIFT_CLASS, verdict=Verdict.INFORMATIONAL.value,
            doctype=DOCTYPE, name=row["name"], owning_app_proposed="",
            fixture_path_proposed="",
            promotion_strategy=PromotionStrategy.NONE.value,
            row_data=row,
        )
        for row in rows
    ]
