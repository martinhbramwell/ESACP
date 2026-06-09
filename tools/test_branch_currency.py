#!/usr/bin/env python3
"""Colocated test for branch_currency.classify (#673) — pure, offline core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.branch_currency import classify  # noqa: E402


def test_umbrella_behind_is_fail():
    level, msg = classify("umbrella/v16-clean-run", 30, is_umbrella=True)
    assert level == "fail"
    assert "30 commit" in msg


def test_umbrella_current_is_ok():
    level, _ = classify("umbrella/v16-clean-run", 0, is_umbrella=True)
    assert level == "ok"


def test_feature_branch_behind_is_warn_not_fail():
    # A working branch a few commits behind main is rebase-before-merge, not yet wrong.
    level, msg = classify("feat/673-x", 3, is_umbrella=False)
    assert level == "warn"
    assert "rebase before merge" in msg


def test_feature_branch_current_is_ok():
    level, _ = classify("feat/673-x", 0, is_umbrella=False)
    assert level == "ok"


def test_unknown_count_is_warn_never_silent_ok():
    # A failed rev-list must surface as a warn, never be masked into a false "current".
    level, msg = classify("umbrella/x", None, is_umbrella=True)
    assert level == "warn"
    assert "unknown" in msg


if __name__ == "__main__":
    from tools.testkit import run_module_tests
    raise SystemExit(run_module_tests(globals()))
