"""Class 5.10 — Translation. DB scan vs <app>/translations/<lang>.csv."""

from __future__ import annotations

from tools.customisation_audit import app_inventory, attribution, db_query
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift, stable_id
from tools.customisation_audit.verdict import PromotionStrategy, Verdict

DRIFT_CLASS = "translation"
DOCTYPE = "Translation"
SQL = "SELECT name, language, source_text, translated_text FROM `tabTranslation`"


def _csv_sources(apps: list[str], lang: str) -> set[str]:
    """Set of source_text values present in any bespoke app's <lang>.csv."""
    out: set[str] = set()
    for app in apps:
        path = app_inventory.app_dir(app) / app / "translations" / f"{lang}.csv"
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            cells = line.split(",", 1)
            if cells:
                out.add(cells[0].strip().strip('"'))
    return out


def run(config: AuditConfig) -> list[Drift]:
    rows = db_query.run_query(config.ssh_host, config.site_config_path, SQL)
    drifts: list[Drift] = []
    csv_cache: dict[str, set[str]] = {}
    for row in rows:
        lang = row.get("language", "")
        if lang not in csv_cache:
            csv_cache[lang] = _csv_sources(config.bespoke_apps, lang)
        if row.get("source_text", "") in csv_cache[lang]:
            continue
        entry = attribution.lookup(config.attribution_map, DRIFT_CLASS, row["name"])
        owning = entry["owning_app"] if entry else ""
        strategy = entry["promotion_strategy"] if entry else PromotionStrategy.APP_TRANSLATIONS_CSV.value
        drifts.append(Drift(
            id=stable_id(DRIFT_CLASS, row["name"], lang, row.get("source_text", "")),
            drift_class=DRIFT_CLASS, verdict=Verdict.DB_ONLY.value,
            doctype=DOCTYPE, name=row["name"], owning_app_proposed=owning,
            fixture_path_proposed="", promotion_strategy=strategy, row_data=row,
        ))
    return drifts
