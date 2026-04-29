#!/usr/bin/env python3
"""Tests for discover_server_script — enumerate-only verdict."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import db_query, discover_server_script as mod  # noqa: E402
from tools.customisation_audit._test_support import patched  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402


def test_enumerate_only_verdict() -> None:
    cfg = AuditConfig("x", "x", [], {})
    rows = [{"name": "ss-1", "script_type": "DocType Event",
             "reference_doctype": "Sales Invoice", "disabled": "0", "module": "CE-SRI"}]
    with patched(db_query, "run_query", lambda *a, **k: rows):
        out = mod.run(cfg)
    assert len(out) == 1
    assert out[0].verdict == "enumerate_only"
    assert out[0].promotion_strategy == "none"


if __name__ == "__main__":
    test_enumerate_only_verdict()
    print("OK test_discover_server_script")
