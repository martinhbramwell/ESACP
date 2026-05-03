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


if __name__ == "__main__":
    sys.exit(0 if test_bench_migrate_is_site_scoped() else 1)
