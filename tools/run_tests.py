#!/usr/bin/env python3
"""Colocated test-suite runner (ESACP#663).

Discovers every ``test_*.py`` under ``tools/`` (excluding ``tools/vm_scripts/``,
which is VM-deployed code, not a controller test) and runs each **as an
executable** — ``./path/test_x.py``. Invoking by path (not ``python3 file``)
is deliberate: a missing ``+x`` bit or shebang surfaces as a failure instead
of being silently masked. Aggregates results; exits non-zero on any failure.

Dependency-free. The authoritative gate (CI + sync_check) calls this script.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_ROOT = REPO_ROOT / "tools"
EXCLUDE_DIRS = ("vm_scripts",)  # VM-deployed code; runs on the guest, not here
PER_TEST_TIMEOUT = 120


def discover() -> list[Path]:
    """All test_*.py under tools/, minus excluded subtrees, sorted."""
    found = [
        p for p in TESTS_ROOT.rglob("test_*.py")
        if not any(part in EXCLUDE_DIRS for part in p.relative_to(REPO_ROOT).parts)
    ]
    return sorted(found)


def runnability_error(path: Path) -> str | None:
    """Return why *path* can't be invoked as an executable, or None if it can."""
    import os
    first = path.open(encoding="utf-8").readline()
    if not first.startswith("#!"):
        return "no shebang — not invokable as ./path (see feedback_invoke_as_executable)"
    if not os.access(path, os.X_OK):
        return "not executable — missing +x bit (chmod +x)"
    return None


def run_one(path: Path) -> tuple[bool, str]:
    """Run a single test as ./path; return (passed, last_output_line)."""
    err = runnability_error(path)
    if err:
        return False, err
    proc = subprocess.run(
        [str(path)], cwd=REPO_ROOT, capture_output=True, text=True,
        timeout=PER_TEST_TIMEOUT,
    )
    if proc.returncode == 0:
        return True, "ok"
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return False, tail[-1] if tail else f"exit {proc.returncode}"


def main() -> int:
    tests = discover()
    failures: list[tuple[Path, str]] = []
    for path in tests:
        rel = path.relative_to(REPO_ROOT)
        try:
            passed, detail = run_one(path)
        except subprocess.TimeoutExpired:
            passed, detail = False, f"timed out after {PER_TEST_TIMEOUT}s"
        mark = "ok  " if passed else "FAIL"
        print(f"  {mark}  {rel}" + ("" if passed else f"  :: {detail}"))
        if not passed:
            failures.append((rel, detail))

    print()
    print(f"  {len(tests) - len(failures)}/{len(tests)} test files passed")
    if failures:
        print(f"  ❌ {len(failures)} failing:")
        for rel, detail in failures:
            print(f"      {rel}  :: {detail}")
        return 1
    print("  ✅ all green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
