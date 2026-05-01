#!/usr/bin/env python3
"""Tests for source_tree_gate — refuse-if-dirty + stage+diff."""

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.customisation_audit import source_tree_gate  # noqa: E402


def _init_repo(td: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(td)], check=True)
    subprocess.run(["git", "-C", str(td), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(td), "config", "user.name", "t"], check=True)
    seed = td / "seed.txt"
    seed.write_text("seed\n")
    subprocess.run(["git", "-C", str(td), "add", "."], check=True)
    # Tempdir-only fixture commit; gpg signing disabled to avoid agent timeout.
    subprocess.run(
        ["git", "-C", str(td), "-c", "commit.gpgsign=false",
         "commit", "-q", "-m", "seed"],
        check=True,
    )
    return td


def test_assert_clean_passes_when_target_paths_clean() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = _init_repo(Path(td))
        target = repo / "new.json"  # not yet written → not dirty
        source_tree_gate.assert_clean([target])  # no exit


def test_assert_clean_exits_2_when_target_path_dirty() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = _init_repo(Path(td))
        seed = repo / "seed.txt"
        seed.write_text("modified\n")  # makes seed.txt dirty
        try:
            source_tree_gate.assert_clean([seed])
            raise AssertionError("expected SystemExit")
        except SystemExit as exc:
            assert exc.code == 2


def test_assert_clean_ignores_dirty_outside_target_paths() -> None:
    """Dirtiness in untargeted paths must not block — only target paths matter."""
    with tempfile.TemporaryDirectory() as td:
        repo = _init_repo(Path(td))
        (repo / "seed.txt").write_text("dirty in untargeted file\n")
        target = repo / "new.json"
        source_tree_gate.assert_clean([target])  # no exit


def test_stage_and_print_diff_stages_new_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = _init_repo(Path(td))
        target = repo / "new.json"
        target.write_text("new\n")
        source_tree_gate.stage_and_print_diff([target])
        out = subprocess.run(
            ["git", "-C", str(repo), "diff", "--cached", "--name-only"],
            capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()
        assert "new.json" in out


def test_stage_and_print_diff_does_not_commit() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = _init_repo(Path(td))
        target = repo / "new.json"
        target.write_text("new\n")
        before = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        source_tree_gate.stage_and_print_diff([target])
        after = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert before == after, "must never commit"


if __name__ == "__main__":
    test_assert_clean_passes_when_target_paths_clean()
    test_assert_clean_exits_2_when_target_path_dirty()
    test_assert_clean_ignores_dirty_outside_target_paths()
    test_stage_and_print_diff_stages_new_file()
    test_stage_and_print_diff_does_not_commit()
    print("OK test_source_tree_gate")
