#!/usr/bin/env python3
"""Colocated test for deflection_lint.flag_lines (#675) — pure, offline core."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.deflection_lint import flag_lines  # noqa: E402


def test_catches_the_plan_didnt_foresee():
    # The exact S116 phrase that triggered the operator's correction.
    hits = flag_lines("the plan didn't foresee that main moved 30 commits")
    assert len(hits) >= 1


def test_catches_nobody_reconciled():
    hits = flag_lines("two divergent copies that nobody reconciled")
    assert len(hits) == 1
    assert "nobody reconciled" in hits[0][1].lower()


def test_catches_bit_rot():
    assert flag_lines("this smells of bit-rot beneath the surface")
    assert flag_lines("the umbrella rotted while main advanced")


def test_legit_config_drift_is_not_flagged():
    # Conservative by design: bare "drift"/"decay" have legitimate technical uses.
    assert flag_lines("sync_check detects configuration drift between hosts") == []
    assert flag_lines("the cache uses exponential decay") == []


def test_agency_owning_sentence_passes():
    # The corrected register: actor + action, no agentless cause.
    assert flag_lines("I cut the branch off a stale umbrella and never rebased it") == []


def test_reports_lineno():
    hits = flag_lines("ok line\nnobody noticed the divergence")
    assert hits[0][0] == 2


if __name__ == "__main__":
    from tools.testkit import run_module_tests
    raise SystemExit(run_module_tests(globals()))
