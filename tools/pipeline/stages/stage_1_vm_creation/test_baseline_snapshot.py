#!/usr/bin/env python3
"""Tests: take_baseline_snapshot delegates to the retry-backed primitive and
fails loudly (ESACP #660 — it used to copy-paste virsh and warn-and-return).
Run directly: ./tools/pipeline/stages/stage_1_vm_creation/test_baseline_snapshot.py."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.stages.stage_1_vm_creation import baseline_snapshot  # noqa: E402


def test_delegates_to_snapshot_or_raise() -> None:
    # No raw subprocess: must route through the hardened primitive, passing the
    # hypervisor alias so the snapshot still runs over SSH (#660 single source).
    with mock.patch.object(baseline_snapshot, "snapshot_or_raise") as sor:
        baseline_snapshot.take_baseline_snapshot("dev15_01", "toshiba", lambda _: None)
    sor.assert_called_once_with("dev15_01", "Baseline", mock.ANY, hypervisor="toshiba")


def test_failure_propagates() -> None:
    # snapshot_or_raise raises on exhausted retries; the unit must NOT swallow it
    # — a missing Baseline silently breaks the stage-1 idempotency gate.
    with mock.patch.object(
        baseline_snapshot, "snapshot_or_raise", side_effect=RuntimeError("boom")
    ):
        try:
            baseline_snapshot.take_baseline_snapshot("dev15_01", "toshiba", lambda _: None)
        except RuntimeError:
            return
    raise AssertionError("take_baseline_snapshot must propagate snapshot failure")


def test_no_raw_subprocess() -> None:
    # The duplicate raw-virsh implementation must be gone (no-duplication rule).
    src = Path(baseline_snapshot.__file__).read_text()
    assert "subprocess" not in src, "raw subprocess must be deleted, not duplicated"
    assert "snapshot-create-as" not in src, "virsh logic must live only in snapshot_ops"


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
