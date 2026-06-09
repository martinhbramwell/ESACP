#!/usr/bin/env python3
"""Colocated test for branch_currency.classify (#673, #684) — pure, offline core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.branch_currency import classify  # noqa: E402


def test_umbrella_behind_is_fail():
    level, msg = classify("umbrella/v16-clean-run", behind=30, ahead=2, is_umbrella=True)
    assert level == "fail"
    assert "30 behind" in msg


def test_umbrella_current_is_ok():
    level, _ = classify("umbrella/v16-clean-run", behind=0, ahead=0, is_umbrella=True)
    assert level == "ok"


def test_feature_branch_behind_is_warn_not_fail():
    # A working branch a few commits behind main is rebase-before-branching, not yet wrong.
    level, msg = classify("feat/684-x", behind=3, ahead=1, is_umbrella=False)
    assert level == "warn"
    assert "rebase before branching off it" in msg


def test_feature_branch_current_is_ok():
    level, _ = classify("feat/684-x", behind=0, ahead=0, is_umbrella=False)
    assert level == "ok"


def test_unknown_behind_is_warn_never_silent_ok():
    # A failed rev-list must surface as a warn, never be masked into a false "current".
    level, msg = classify("umbrella/x", behind=None, ahead=0, is_umbrella=True)
    assert level == "warn"
    assert "unknown" in msg


def test_zero_unique_reads_safe_to_retire_not_stale():
    # The S116 lesson: far behind != obsolete. 255 behind but 0 unique commits =>
    # content already on main, safe to retire — the message must SAY that.
    level, msg = classify("umbrella/erpnext-idiomatic-refactor", behind=255, ahead=0, is_umbrella=True)
    assert level == "fail"          # base-currency: still not a branch to build off
    assert "0 unique commits" in msg and "safe to retire" in msg


def test_unmerged_work_is_flagged_for_assessment():
    # A branch with unique commits must never read as disposable on distance alone.
    level, msg = classify("umbrella/ladder-fixture", behind=342, ahead=1, is_umbrella=True)
    assert "1 unmerged commit(s)" in msg
    assert "ASSESS before retiring" in msg


if __name__ == "__main__":
    from tools.testkit import run_module_tests
    raise SystemExit(run_module_tests(globals()))
