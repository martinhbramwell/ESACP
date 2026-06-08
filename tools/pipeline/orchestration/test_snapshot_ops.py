#!/usr/bin/env python3
"""Tests: create_snapshot retry + snapshot_or_raise no-masking (ESACP #658).
Run directly: ./tools/pipeline/orchestration/test_snapshot_ops.py (exit 0/1)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.orchestration import snapshot_ops  # noqa: E402


def _result(returncode: int, stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)


def _patch(run_kw):
    return (mock.patch.object(snapshot_ops.subprocess, "run", **run_kw),
            mock.patch.object(snapshot_ops.time, "sleep"))


def test_success_first_attempt_no_sleep() -> None:
    run_p, sleep_p = _patch({"return_value": _result(0)})
    with run_p as run, sleep_p as sleep:
        ok = snapshot_ops.create_snapshot("dev15_01", "Baseline", lambda _: None)
    assert ok is True
    assert run.call_count == 1 and sleep.call_count == 0   # no needless retry


def test_retry_then_success() -> None:
    # First attempt fails transiently, second wins — the #658 scenario.
    side = [_result(1, "Extra element disks in interleave"), _result(0)]
    run_p, sleep_p = _patch({"side_effect": side})
    with run_p as run, sleep_p as sleep:
        ok = snapshot_ops.create_snapshot("dev15_01", "Baseline", lambda _: None)
    assert ok is True
    assert run.call_count == 2 and sleep.call_count == 1   # backed off once


def test_exhausted_returns_false() -> None:
    lines: list[str] = []
    run_p, sleep_p = _patch({"return_value": _result(1, "boom")})
    with run_p as run, sleep_p as sleep:
        ok = snapshot_ops.create_snapshot("dev15_01", "Baseline", lines.append)
    assert ok is False                                     # no masking upward
    assert run.call_count == 3 and sleep.call_count == 2   # slept between only
    assert any("failed after 3 attempts" in ln for ln in lines)


def test_snapshot_or_raise_is_fatal() -> None:
    run_p, sleep_p = _patch({"return_value": _result(1, "boom")})
    with run_p, sleep_p:
        try:
            snapshot_ops.snapshot_or_raise("dev15_01", "Baseline", lambda _: None)
        except RuntimeError:
            return
    raise AssertionError("snapshot_or_raise must raise on snapshot failure")


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
