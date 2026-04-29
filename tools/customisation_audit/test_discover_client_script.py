#!/usr/bin/env python3
"""Tests for discover_client_script."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import (  # noqa: E402
    db_query, discover_client_script as mod, target_resolution,
)
from tools.customisation_audit._test_support import patched  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402
from tools.customisation_audit.drift import Drift  # noqa: E402


def test_db_only_when_no_js_file() -> None:
    cfg = AuditConfig("x", "x", ["ce_sri"], {})
    rows = [{"name": "Sales Invoice-validate", "dt": "Sales Invoice",
             "view": "Form", "script": "frappe.ui.form.on(...)", "enabled": "1",
             "module": "CE-SRI"}]
    # _file_exists_for returns None because no scaffolded apps; resolve returns "ce_sri"
    with patched(db_query, "run_query", lambda *a, **k: rows), \
         patched(target_resolution, "module_to_app", lambda apps: {"CE-SRI": "ce_sri"}):
        out = mod.run(cfg)
    assert len(out) == 1 and isinstance(out[0], Drift)
    assert out[0].verdict == "db_only"
    assert out[0].promotion_strategy == "fixtures_custom_scripts"


if __name__ == "__main__":
    test_db_only_when_no_js_file()
    print("OK test_discover_client_script")
