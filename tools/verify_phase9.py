#!/usr/bin/env python3
"""Acceptance test for Phase 9 (#197) — install_specific.py decomposition.

Verifies the thin entry is ≤50 lines, each package file is ≤80 lines,
the stdlib-only constraint holds (no `requests`), the pipeline-reachable
subcommands are importable through the entry, and prior phases still pass.

Exit 0 on pass, 1 on first failure (prints all). Usage: ``./tools/verify_phase9.py``
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "tools" / "install_specific.py"
PKG = REPO / "tools" / "vm_scripts" / "install_specific"

ENTRY_CAP = 50
PKG_CAP = 80


def _wc(path: Path) -> int:
    return sum(1 for _ in path.open())


def check_entry_size() -> list[str]:
    if not ENTRY.exists():
        return [f"[FAIL] {ENTRY.relative_to(REPO)} missing"]
    n = _wc(ENTRY)
    if n > ENTRY_CAP:
        return [f"[FAIL] tools/install_specific.py: {n} > {ENTRY_CAP}"]
    print(f"[OK]   tools/install_specific.py: {n} ≤ {ENTRY_CAP}")
    return []


def check_package_present() -> list[str]:
    if not PKG.is_dir():
        return [f"[FAIL] {PKG.relative_to(REPO)}/ missing"]
    if not (PKG / "__init__.py").exists():
        return [f"[FAIL] {PKG.relative_to(REPO)}/__init__.py missing"]
    print(f"[OK]   {PKG.relative_to(REPO)}/ present")
    return []


def check_package_file_sizes() -> list[str]:
    fails = []
    for py in sorted(PKG.rglob("*.py")):
        n = _wc(py)
        rel = py.relative_to(REPO)
        if n > PKG_CAP:
            fails.append(f"[FAIL] {rel}: {n} > {PKG_CAP}")
    if not fails:
        count = sum(1 for _ in PKG.rglob("*.py"))
        print(f"[OK]   all {count} package files ≤ {PKG_CAP}")
    return fails


def check_stdlib_only() -> list[str]:
    r = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-E",
         r"^\s*(import|from)\s+requests(\s|\.|$)",
         str(ENTRY), str(PKG)],
        capture_output=True, text=True,
    )
    fails = [f"[FAIL] `requests` import: {line}" for line in r.stdout.splitlines()]
    if not fails:
        print("[OK]   stdlib-only (no `requests` import)")
    return fails


def check_commands_importable() -> list[str]:
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, str('"
         + str(PKG.parent) + "')); "
         "from install_specific import "
         "cmd_before_install, cmd_after_restart; "
         "print('imports ok')"],
        capture_output=True, text=True, cwd=REPO,
    )
    if r.returncode != 0:
        return [f"[FAIL] package import failed:\n{r.stderr.strip()}"]
    print("[OK]   both cmd_* importable through the package")
    return []


def check_entry_help() -> list[str]:
    r = subprocess.run(
        [str(ENTRY), "--help"], capture_output=True, text=True, cwd=REPO,
    )
    if r.returncode != 0:
        return [f"[FAIL] ./tools/install_specific.py --help failed:\n{r.stderr}"]
    expected = ["before-install", "after-restart"]
    missing = [cmd for cmd in expected if cmd not in r.stdout]
    if missing:
        return [f"[FAIL] --help missing subcommands: {missing}"]
    print("[OK]   ./tools/install_specific.py --help lists both subcommands")
    return []


def check_prior_phases() -> list[str]:
    fails = []
    for phase in ("verify_phase7.py", "verify_phase8.py"):
        r = subprocess.run(
            [str(REPO / "tools" / phase)], capture_output=True, text=True,
        )
        if r.returncode != 0:
            fails.append(f"[FAIL] {phase} regressed:\n{r.stdout}\n{r.stderr}")
        else:
            print(f"[OK]   {phase} still passes")
    return fails


def main() -> int:
    fails = []
    fails += check_entry_size()
    fails += check_package_present()
    fails += check_package_file_sizes()
    fails += check_stdlib_only()
    fails += check_commands_importable()
    fails += check_entry_help()
    fails += check_prior_phases()
    if fails:
        print()
        for f in fails:
            print(f)
        return 1
    print("\n✅  Phase 9 acceptance — all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
