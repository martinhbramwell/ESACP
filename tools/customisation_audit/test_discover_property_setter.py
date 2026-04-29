#!/usr/bin/env python3
"""Tests for discover_property_setter."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import (  # noqa: E402
    app_inventory, db_query, discover_property_setter as mod, target_resolution,
)
from tools.customisation_audit._test_support import patched  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402
from tools.customisation_audit.drift import Drift  # noqa: E402


def test_db_only_emitted() -> None:
    cfg = AuditConfig("x", "x", ["ce_sri"], {})
    rows = [{"name": "Sales Invoice-status-options", "doc_type": "Sales Invoice",
             "field_name": "status", "property": "options", "value": "X\nY",
             "property_type": "Text", "module": "CE-SRI"}]
    with patched(db_query, "run_query", lambda *a, **k: rows), \
         patched(app_inventory, "load_fixture_file", lambda *a, **k: []), \
         patched(target_resolution, "module_to_app", lambda apps: {"CE-SRI": "ce_sri"}):
        out = mod.run(cfg)
    assert len(out) == 1 and isinstance(out[0], Drift)
    assert out[0].verdict == "db_only"


if __name__ == "__main__":
    test_db_only_emitted()
    print("OK test_discover_property_setter")
