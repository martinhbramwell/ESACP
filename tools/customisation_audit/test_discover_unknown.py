#!/usr/bin/env python3
"""Tests for discover_unknown — Phase 1 stub returns empty list."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import discover_unknown as mod  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402


def test_stub_returns_empty_list() -> None:
    cfg = AuditConfig("x", "x", [], {})
    assert mod.run(cfg) == []


if __name__ == "__main__":
    test_stub_returns_empty_list()
    print("OK test_discover_unknown")
