#!/usr/bin/env python3
"""Tests for discover_print_format."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import (  # noqa: E402
    db_query, discover_print_format as mod, target_resolution,
)
from tools.customisation_audit._test_support import patched  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402
from tools.customisation_audit.drift import Drift  # noqa: E402


def test_db_only_with_v14_patch_strategy() -> None:
    cfg = AuditConfig("x", "x", ["ce_sri"], {})
    rows = [{"name": "Custom Invoice PF", "doc_type": "Sales Invoice",
             "module": "CE-SRI", "standard": "No", "disabled": "0"}]
    with patched(db_query, "run_query", lambda *a, **k: rows), \
         patched(target_resolution, "module_to_app", lambda apps: {"CE-SRI": "ce_sri"}):
        out = mod.run(cfg)
    assert len(out) == 1 and isinstance(out[0], Drift)
    assert out[0].verdict == "db_only"
    assert out[0].promotion_strategy == "v14_patch_script"


if __name__ == "__main__":
    test_db_only_with_v14_patch_strategy()
    print("OK test_discover_print_format")
