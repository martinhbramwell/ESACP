#!/usr/bin/env python3
"""Tests: build-watch exit classification — the #637 regression guard.

Run directly: ``./tools/pipeline/orchestration/test_build_template_watch.py``
Exit 0 on pass, 1 on fail. No pytest dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.orchestration.build_template_watch import (  # noqa: E402
    parse_exit,
)


def test_success_is_terminal_zero() -> None:
    assert parse_exit(0, "0\n") == 0


def test_real_nonzero_is_terminal() -> None:
    assert parse_exit(0, "1\n") == 1
    assert parse_exit(0, "137") == 137


def test_minus_one_sentinel_is_pending() -> None:
    # build.sh has not written its exit file yet — keep waiting, never fail.
    assert parse_exit(0, "-1\n") is None


def test_transport_blip_is_pending_not_failure() -> None:
    # The #637 bug: ssh returncode != 0 with empty stdout used to become exit 1.
    assert parse_exit(255, "") is None
    assert parse_exit(255, "-1\n") is None  # remote sentinel never ran


def test_empty_or_garbage_stdout_is_pending() -> None:
    assert parse_exit(0, "") is None
    assert parse_exit(0, "\n") is None
    assert parse_exit(0, "not-a-number") is None


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
