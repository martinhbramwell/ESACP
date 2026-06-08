#!/usr/bin/env python3
"""Pre-commit exec-bit lint (ESACP#663, #666).

Mechanical guard for feedback_invoke_as_executable: any staged shebanged
``tools/**/*.py`` — and every staged ``test_*.py`` — must carry the executable
bit (git index mode 100755). A shebanged-but-non-executable script can't be
invoked by path and silently rots (the #663 root cause). Checks the STAGED
index mode, which is what the commit captures.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _staged_entries() -> list[tuple[str, str]]:
    """Return (mode, path) for staged added/modified files under tools/."""
    out = subprocess.run(
        ["git", "ls-files", "-s", "--", "tools/"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    ).stdout
    staged = set(subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    ).stdout.split())
    entries = []
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        # vm_scripts/ is guest-deployed code (relative imports, never run by
        # path) — excluded here as it is from the runner.
        if path in staged and path.endswith(".py") and "/vm_scripts/" not in path:
            entries.append((meta.split()[0], path))
    return entries


def _has_shebang(path: str) -> bool:
    blob = subprocess.run(
        ["git", "show", f":{path}"], capture_output=True, text=True, cwd=REPO_ROOT,
    ).stdout
    return blob.startswith("#!")


def main() -> int:
    violations = [
        path for mode, path in _staged_entries()
        if mode != "100755"
        and (Path(path).name.startswith("test_") or _has_shebang(path))
    ]
    if violations:
        print("Exec-bit check FAILED — these need `chmod +x` before commit:")
        for path in violations:
            print(f"  {path}")
        print("\nShebanged scripts and test_*.py must be invokable by path"
              " (feedback_invoke_as_executable / #663).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
