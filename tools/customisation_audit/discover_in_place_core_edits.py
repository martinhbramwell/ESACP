"""Phase 4 — discover in-place core-tree edits in apps/{frappe,erpnext}.

Reads from a substrate worktree (production master at design time;
overridable via `ESACP_CORE_TREE_ROOT`). Returns [] when the AuditConfig
has no `core_tree_root` set (graceful skip).
"""
from __future__ import annotations

import os
from pathlib import Path

from tools.customisation_audit import core_diff_classifier, core_tree_diff, in_place_attribution  # noqa: E501
from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.core_tree_config import CoreTreeConfig
from tools.customisation_audit.drift import Drift


def resolve_root(project_root: str) -> str | None:
    """Phase 4 substrate root: env override > <project_root>/../PRODUCTION_20260404/apps."""
    override = os.environ.get("ESACP_CORE_TREE_ROOT")
    if override:
        return override if Path(override).exists() else None
    default = Path(project_root).parent / "PRODUCTION_20260404" / "apps"
    return str(default) if default.exists() else None


def run(config: AuditConfig) -> list[Drift]:
    root = getattr(config, "core_tree_root", None)
    if not root or not Path(root).exists():
        return []
    cc = CoreTreeConfig(substrate_root=root)
    drifts: list[Drift] = []
    for app, rel, diff, before, after in core_tree_diff.iter_modified(cc):
        drifts.extend(core_diff_classifier.classify(app, rel, diff, before, after))
    return in_place_attribution.apply_attribution(drifts, config.attribution_map)
