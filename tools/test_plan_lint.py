#!/usr/bin/env python3
"""Colocated test for plan_lint (#674) — pure, offline cores."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.plan_lint import parse_block, check_creates_host, evaluate  # noqa: E402

HOSTS_MAP = "  kvm:\n    dev15_01:\n      hostname: dev15_01\n    dev02:\n      hostname: dev02\n"

BLOCK = "<!-- plan-check\nbase: umbrella/v16-clean-run\ncreates-host: dev15_01\n-->"


def test_parse_block_extracts_keys():
    d = parse_block(f"intro\n{BLOCK}\nrest")
    assert d["base"] == ["umbrella/v16-clean-run"]
    assert d["creates-host"] == ["dev15_01"]


def test_parse_block_absent_is_none():
    assert parse_block("a plain agenda with no block") is None


def test_creates_host_already_registered_is_fail():
    # The exact S116 trap: plan says "register dev15_01" but main already has it.
    level, msg = check_creates_host("dev15_01", HOSTS_MAP)
    assert level == "fail"
    assert "already in hosts_map" in msg


def test_creates_host_absent_is_ok():
    level, _ = check_creates_host("dev99", HOSTS_MAP)
    assert level == "ok"


def test_evaluate_no_block_soft_passes():
    rows, has_block = evaluate("no block here", HOSTS_MAP)
    assert has_block is False
    assert rows == []


def test_evaluate_flags_stale_creates_host():
    rows, has_block = evaluate(BLOCK, HOSTS_MAP)
    assert has_block is True
    # creates-host dev15_01 is already present → at least one fail row.
    assert any(level == "fail" for level, _ in rows)


if __name__ == "__main__":
    from tools.testkit import run_module_tests
    raise SystemExit(run_module_tests(globals()))
