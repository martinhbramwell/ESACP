#!/usr/bin/env python3
"""Tests: provision_vm acts on each snapshot return — Baseline fatal, Fresh
Install best-effort (ESACP #660 — both returns were silently discarded).
Run directly: ./tools/pipeline/orchestration/test_ansible_provision.py (exit 0/1)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.orchestration import ansible_provision as ap  # noqa: E402


def _provision(snapshot_results):
    """Run provision_vm with everything stubbed green except create_snapshot,
    which returns successive values from *snapshot_results*. Returns (ok, lines)."""
    lines: list[str] = []
    with mock.patch.object(ap, "ansible_ping", return_value=True), \
         mock.patch.object(ap, "run_playbook", return_value=True), \
         mock.patch.object(ap, "list_snapshots", return_value=[]), \
         mock.patch.object(ap, "create_snapshot", side_effect=snapshot_results) as snap:
        ok = ap.provision_vm(
            "dev15_01", "toshiba", "/repo", "/key", lines.append,
        )
    return ok, lines, snap


def test_baseline_failure_is_fatal() -> None:
    # Fresh Install ok, Baseline fails → provision must report failure (#660).
    ok, lines, _ = _provision([True, False])
    assert ok is False, "Baseline snapshot failure must fail the provision"
    assert any("provision failed" in ln for ln in lines)


def test_fresh_install_failure_is_best_effort() -> None:
    # Fresh Install fails, Baseline ok → provision still succeeds (non-fatal).
    ok, lines, _ = _provision([False, True])
    assert ok is True, "Fresh Install checkpoint failure must NOT fail provision"
    assert any("non-fatal" in ln for ln in lines)


def test_happy_path() -> None:
    ok, _lines, snap = _provision([True, True])
    assert ok is True
    assert snap.call_count == 2   # Fresh Install + Baseline both attempted


def _run() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL {name}: {exc}")
    print(f"\n{'OK' if not failures else f'{failures} FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
