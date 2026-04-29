"""Audit orchestration — load substrate config, iterate discover modules, emit report."""

from __future__ import annotations

import yaml
from pathlib import Path

from tools.customisation_audit import (
    attribution, db_query, delta_report, discover_client_script,
    discover_custom_docperm, discover_custom_doctype, discover_custom_field,
    discover_naming_series, discover_print_format, discover_property_setter,
    discover_server_script, discover_translation, discover_unknown,
    discover_workflow,
)
from tools.customisation_audit.audit_config import AuditConfig
from tools.pipeline.stages.common.config import build_config

DISCOVER_MODULES = [
    discover_custom_field, discover_property_setter, discover_client_script,
    discover_print_format, discover_workflow, discover_custom_docperm,
    discover_translation, discover_server_script, discover_custom_doctype,
    discover_naming_series, discover_unknown,
]
BESPOKE_APPS = ["ce_sri", "returnable", "route_planner"]


def _build_audit_config(hostname: str, project_root: str) -> AuditConfig:
    with open(Path(project_root) / "hosts_map.yml") as fh:
        hosts = yaml.safe_load(fh)
    host_cfg = hosts.get("groups", {}).get("kvm", {}).get(hostname)
    if not host_cfg:
        raise RuntimeError(f"{hostname!r} not found in hosts_map.yml/groups/kvm")
    cfg = build_config(hostname, host_cfg, project_root, use_wg=True)
    site_config = f"{cfg.bench_dir}/sites/{cfg.site_url}/site_config.json"
    amap = attribution.load(Path(project_root) / attribution.DEFAULT_PATH)
    return AuditConfig(
        ssh_host=f"{hostname}-erp",
        site_config_path=site_config,
        bespoke_apps=BESPOKE_APPS,
        substrate_meta={"vm": hostname, "site_url": cfg.site_url},
        attribution_map=amap,
    )


def run_audit(hostname: str, project_root: str) -> dict:
    """Discover all customisation drifts on hostname; return delta-report dict."""
    cfg = _build_audit_config(hostname, project_root)
    db_query.deploy_runner(cfg.ssh_host)
    drifts = [d for module in DISCOVER_MODULES for d in module.run(cfg)]
    return delta_report.emit(drifts, cfg.substrate_meta)
