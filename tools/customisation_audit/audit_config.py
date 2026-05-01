"""Runtime configuration for discovery — passed to each discover_*.run()."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditConfig:
    """Runtime settings consumed by every discover_*.py module."""

    ssh_host: str           # SSH alias, e.g. "dev01-erp"
    site_config_path: str   # remote absolute path to site_config.json
    bespoke_apps: list[str] # e.g. ["ce_sri", "returnable", "route_planner"]
    substrate_meta: dict    # populated into the report's "substrate" header
    attribution_map: dict = field(default_factory=dict)
    """Operator-curated drift-class → name → {owning_app, strategy}; see attribution.py."""
    core_tree_root: str | None = None
    """Phase 4 substrate root (apps/{frappe,erpnext} parent). None → skip Phase 4."""
