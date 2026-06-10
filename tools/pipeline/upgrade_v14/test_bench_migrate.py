#!/usr/bin/env python3
"""bench_migrate emits a site-scoped command."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import tools.pipeline.upgrade_v14.bench_migrate as bench_migrate  # noqa: E402
from tools.pipeline.upgrade_v14._test_helpers import make_config, ok, patch_ssh  # noqa: E402


def test_bench_migrate_is_site_scoped() -> bool:
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        return ok()

    orig = patch_ssh(bench_migrate, fake)
    try:
        result = bench_migrate.run_bench_migrate(make_config(), lambda _: None)
    finally:
        bench_migrate.ssh_run = orig
    if not result.success:
        print(f"FAIL: {result.message}")
        return False
    if not any("bench --site dev01.iridium.blue migrate" in c for c in captured):
        print(f"FAIL: expected site-scoped migrate command:\n{captured}")
        return False
    print("PASS: bench_migrate is site-scoped")
    return True


def test_bench_migrate_pauses_writers_before_migrate() -> bool:
    """#691: maintenance-mode on + scheduler pause must precede migrate."""
    captured: list[str] = []

    def fake(_cfg, cmd, *, timeout=30):
        captured.append(cmd)
        return ok()

    orig = patch_ssh(bench_migrate, fake)
    try:
        bench_migrate.run_bench_migrate(make_config(), lambda _: None)
    finally:
        bench_migrate.ssh_run = orig
    idx_maint = next((i for i, c in enumerate(captured) if "set-maintenance-mode on" in c), -1)
    idx_pause = next((i for i, c in enumerate(captured) if "scheduler pause" in c), -1)
    idx_migrate = next((i for i, c in enumerate(captured) if "migrate" in c and "set-maintenance" not in c), -1)
    if idx_maint < 0 or idx_pause < 0:
        print(f"FAIL: missing maintenance-on/scheduler-pause:\n{captured}")
        return False
    if not (idx_maint < idx_migrate and idx_pause < idx_migrate):
        print(f"FAIL: pause must precede migrate:\n{captured}")
        return False
    print("PASS: bench_migrate pauses writers before migrate")
    return True


if __name__ == "__main__":
    ok_all = (
        test_bench_migrate_is_site_scoped()
        and test_bench_migrate_pauses_writers_before_migrate()
    )
    sys.exit(0 if ok_all else 1)
