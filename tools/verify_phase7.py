#!/usr/bin/env python3
"""Acceptance test for Phase 7 (#195) — dispatcher layer thin-out.

Verifies the CLAUDE.md anti-spiral caps and the no-subprocess rule for the
three dispatcher surfaces. Exit 0 on pass, 1 on first failure (prints all).

Usage: ``./tools/verify_phase7.py``
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


CAPS = [
    ("tools/esacp.py",        150),
    ("tools/api/__init__.py", 300),
    ("tools/job_worker.py",   100),
]

# Hard caps for files created in Phase 7. Existing tools/pipeline/ files are
# grandfathered by the ratchet (see tools/pre_commit_size_check.py); new
# pipeline files added going forward are capped at 80 by that hook.
CATEGORY_CAPS = [
    ("tools/cli",         80),
    ("tools/api",         80),
]

# Files allowed to call subprocess.run/Popen inside the dispatcher surfaces.
SUBPROCESS_EXCEPTIONS = {
    "tools/api/jobs.py",        # spawn_job (Popen) — documented GH #37
}


def _count_lines(path: Path) -> int:
    return sum(1 for _ in path.open())


def check_target_caps() -> list[str]:
    fails = []
    for rel, cap in CAPS:
        lines = _count_lines(REPO / rel)
        if lines > cap:
            fails.append(f"[FAIL] {rel}: {lines} lines > {cap}")
        else:
            print(f"[OK]   {rel}: {lines} ≤ {cap}")
    return fails


def check_category_caps() -> list[str]:
    fails = []
    for prefix, cap in CATEGORY_CAPS:
        for path in sorted((REPO / prefix).rglob("*.py")):
            lines = _count_lines(path)
            rel = path.relative_to(REPO).as_posix()
            if lines > cap:
                fails.append(f"[FAIL] {rel}: {lines} lines > {cap}")
    if not fails:
        print(f"[OK]   all {', '.join(p for p, _ in CATEGORY_CAPS)}/*.py ≤ 80")
    return fails


def check_no_subprocess() -> list[str]:
    fails = []
    targets = ["tools/esacp.py", "tools/api/", "tools/cli/", "tools/job_worker.py"]
    r = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-E", r"subprocess\.(run|Popen)", *targets],
        cwd=REPO, capture_output=True, text=True,
    )
    for line in r.stdout.splitlines():
        rel = line.split(":", 1)[0]
        if rel in SUBPROCESS_EXCEPTIONS:
            continue
        # tools/cli/verify_*.py are SUT integration harnesses, not dispatchers —
        # they invoke the built esacp.py CLI under test (GH #275).
        if rel.startswith("tools/cli/verify_") and rel.endswith(".py"):
            continue
        fails.append(f"[FAIL] unexpected subprocess call: {line}")
    if not fails:
        print("[OK]   no unauthorised subprocess calls in dispatcher surfaces")
    return fails


def check_cli_help() -> list[str]:
    r = subprocess.run(
        [str(REPO / "tools" / "esacp.py"), "--help"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return [f"[FAIL] esacp.py --help failed: {r.stderr.strip()}"]
    print("[OK]   ./tools/esacp.py --help loads")
    return []


def main() -> int:
    fails = []
    fails += check_target_caps()
    fails += check_category_caps()
    fails += check_no_subprocess()
    fails += check_cli_help()
    if fails:
        print()
        for f in fails:
            print(f)
        return 1
    print("\n✅  Phase 7 acceptance — all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
