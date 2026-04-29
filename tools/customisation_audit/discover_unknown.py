"""Catch-all — anything DM-suspect not covered by the 11 audited classes.

Phase 1 ships this as a stub. The audit (`docs/upgrade/DMCustomisationCapabilityAudit.md`)
identifies 11 classes; future runs that surface table types not in that list should
extend this module with class-specific detection. For now it returns an empty list.

When extended (Phase 2+ feedback), the convention is:
    - Probe DB for tables with rows whose ``modified_by != "Administrator"``
      (or other DM-suspect heuristic).
    - Emit ``Drift`` entries with ``drift_class="unknown"`` and the table name in notes.
"""

from __future__ import annotations

from tools.customisation_audit.audit_config import AuditConfig
from tools.customisation_audit.drift import Drift


def run(config: AuditConfig) -> list[Drift]:
    return []
