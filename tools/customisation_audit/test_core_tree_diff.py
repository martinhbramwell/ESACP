#!/usr/bin/env python3
"""Tests for core_tree_diff — synthetic git repo with known modifications."""

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import core_tree_diff  # noqa: E402
from tools.customisation_audit.core_tree_config import CoreTreeConfig  # noqa: E402


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True)


def _setup_repo(root: Path) -> Path:
    """Build apps/frappe/ with one tracked-modified JSON on branch version-13."""
    app = root / "apps" / "frappe"
    app.mkdir(parents=True)
    _git(["init", "-q"], app)
    _git(["config", "user.email", "t@t"], app)
    _git(["config", "user.name", "t"], app)
    _git(["checkout", "-b", "version-13", "-q"], app)
    f = app / "f.json"
    f.write_text('{"name": "X", "value": 1}\n')
    _git(["add", "."], app)
    _git(["commit", "-qm", "init"], app)
    f.write_text('{"name": "X", "value": 2}\n')
    return root / "apps"


def test_iter_modified_yields_diff_before_after() -> None:
    with tempfile.TemporaryDirectory() as td:
        substrate = _setup_repo(Path(td))
        cc = CoreTreeConfig(substrate_root=str(substrate), apps=["frappe"])
        rows = list(core_tree_diff.iter_modified(cc))
    assert len(rows) == 1
    app, rel, diff, before, after = rows[0]
    assert app == "frappe" and rel == "f.json"
    assert "value" in diff and '"value": 1' in before and '"value": 2' in after


if __name__ == "__main__":
    test_iter_modified_yields_diff_before_after()
    print("OK test_core_tree_diff")
