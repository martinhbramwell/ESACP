#!/usr/bin/env python3
"""Tests: per-major template naming + target_frappe_major selection (#631).

Run directly: ``./tools/pipeline/orchestration/test_template_metadata.py``
Exit 0 on pass, 1 on fail. No pytest dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.pipeline.orchestration.load_host_config import (  # noqa: E402
    DEFAULT_FRAPPE_MAJOR, target_frappe_major,
)
from tools.pipeline.orchestration.template_metadata import (  # noqa: E402
    DEFAULT_MAJOR, metadata_basename, metadata_path,
)


def test_metadata_basename_is_per_major() -> None:
    assert metadata_basename(15) == "erpnext-v15-latest.json"
    assert metadata_basename(16) == "erpnext-v16-latest.json"
    # The dual-template lines never collide on a filename.
    assert metadata_basename(13) != metadata_basename(15)


def test_metadata_basename_default_is_v13() -> None:
    assert DEFAULT_MAJOR == 13
    assert metadata_basename() == "erpnext-v13-latest.json"


def test_metadata_path_joins_dir_and_basename() -> None:
    assert metadata_path(15).endswith("/erpnext-v15-latest.json")
    assert metadata_path(15) == metadata_path(15)  # deterministic


def test_target_major_reads_attribute() -> None:
    assert target_frappe_major({"target_frappe_major": 15}) == 15
    assert target_frappe_major({"target_frappe_major": "16"}) == 16  # yaml-as-str


def test_target_major_defaults_to_13() -> None:
    assert DEFAULT_FRAPPE_MAJOR == 13
    assert target_frappe_major({}) == 13


def test_selector_round_trip() -> None:
    # The number a host targets is the template line it clones.
    host_cfg = {"target_frappe_major": 15}
    major = target_frappe_major(host_cfg)
    assert metadata_basename(major) == "erpnext-v15-latest.json"


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
