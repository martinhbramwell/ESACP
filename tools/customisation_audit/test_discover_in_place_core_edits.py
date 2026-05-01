#!/usr/bin/env python3
"""Tests for discover_in_place_core_edits — graceful skip + integration."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import discover_in_place_core_edits as mod  # noqa: E402
from tools.customisation_audit.audit_config import AuditConfig  # noqa: E402


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True)


def test_returns_empty_when_core_tree_root_is_none() -> None:
    cfg = AuditConfig(ssh_host="", site_config_path="", bespoke_apps=[],
                      substrate_meta={}, core_tree_root=None)
    assert mod.run(cfg) == []


def test_returns_empty_when_core_tree_root_does_not_exist() -> None:
    cfg = AuditConfig(ssh_host="", site_config_path="", bespoke_apps=[],
                      substrate_meta={}, core_tree_root="/nonexistent/path/xyz")
    assert mod.run(cfg) == []


def test_resolve_root_env_override(tmp_path=None) -> None:
    with tempfile.TemporaryDirectory() as td:
        os.environ["ESACP_CORE_TREE_ROOT"] = td
        try:
            assert mod.resolve_root("/anywhere") == td
        finally:
            os.environ.pop("ESACP_CORE_TREE_ROOT", None)


def test_integration_discovers_synthetic_modification() -> None:
    with tempfile.TemporaryDirectory() as td:
        app = Path(td) / "frappe"
        app.mkdir()
        _git(["init", "-q"], app)
        _git(["config", "user.email", "t@t"], app)
        _git(["config", "user.name", "t"], app)
        _git(["checkout", "-b", "version-13", "-q"], app)
        (app / "x.py").write_text("a = 1\n")
        _git(["add", "."], app)
        _git(["commit", "-qm", "init"], app)
        (app / "x.py").write_text("a = 2\n")
        cfg = AuditConfig(ssh_host="", site_config_path="", bespoke_apps=[],
                          substrate_meta={}, core_tree_root=td)
        drifts = mod.run(cfg)
    assert len(drifts) == 1 and drifts[0].verdict == "human_review_core_edit"


if __name__ == "__main__":
    test_returns_empty_when_core_tree_root_is_none()
    test_returns_empty_when_core_tree_root_does_not_exist()
    test_resolve_root_env_override()
    test_integration_discovers_synthetic_modification()
    print("OK test_discover_in_place_core_edits")
