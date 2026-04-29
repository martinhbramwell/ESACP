#!/usr/bin/env python3
"""Tests for discover_custom_docperm."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import (  # noqa: E402
    db_query, discover_custom_docperm as mod, target_resolution,
)
from tools.customisation_audit._test_support import patched  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402
from tools.customisation_audit.drift import Drift  # noqa: E402


def test_db_only_with_manual_strategy_when_no_owning_app() -> None:
    cfg = AuditConfig("x", "x", [], {})
    rows = [{"name": "perm-1", "parent": "Sales Invoice", "role": "Accounts User",
             "permlevel": "0", "read": "1", "write": "1", "create": "1", "delete": "0",
             "submit": "1", "cancel": "0", "amend": "0", "if_owner": "0"}]
    with patched(db_query, "run_query", lambda *a, **k: rows), \
         patched(target_resolution, "module_to_app", lambda apps: {}):
        out = mod.run(cfg)
    assert len(out) == 1 and isinstance(out[0], Drift)
    assert out[0].verdict == "db_only"
    assert out[0].promotion_strategy == "manual"


if __name__ == "__main__":
    test_db_only_with_manual_strategy_when_no_owning_app()
    print("OK test_discover_custom_docperm")
