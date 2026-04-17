#!/usr/bin/env python3
"""Acceptance test for Phase 8 (#196) — dead Gen 1 orchestrator deletion.

Verifies the Gen-1 dev-CRUD orchestrators are gone, no Python code imports
``orchestration``, no live operator doc instructs the reader to run a
deleted script, and Phase 7's invariants are still intact.

Exit 0 on pass, 1 on first failure (prints all). Usage: ``./tools/verify_phase8.py``
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


DELETED_FILES = [
    "tools/orchestrator.py",
    "orchestration/provision.py",
    "orchestration/provision_kvm.py",
]

# Historical artifacts where a reference to a deleted path is acceptable
# (a snapshot of past work, not an instruction to the current operator).
DOC_EXCEPTIONS = {
    "SETUP_GUIDE.md",                                # Stage 1, banner added
    "Stage 1.5 completion checklist.md",             # Stage 1.5 retired
    "platforms/vbox/PLATFORM.md",                    # VBox retired
    "design_docs/Stage 2.1 ESACP Plan.md",           # Stage 2.1 historical
}


def check_files_deleted() -> list[str]:
    fails = []
    for rel in DELETED_FILES:
        if (REPO / rel).exists():
            fails.append(f"[FAIL] {rel} still exists — should be deleted")
        else:
            print(f"[OK]   {rel} deleted")
    return fails


def check_no_python_imports() -> list[str]:
    r = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-E",
         r"(^|\s)(from|import)\s+orchestration(\.|\s|$)",
         "tools/", "orchestration/"],
        cwd=REPO, capture_output=True, text=True,
    )
    fails = []
    for line in r.stdout.splitlines():
        fails.append(f"[FAIL] Python import of orchestration: {line}")
    if not fails:
        print("[OK]   no Python imports of orchestration/")
    return fails


def check_no_live_doc_refs() -> list[str]:
    fails = []
    patterns = [p.split("/", 1)[1] if "/" in p else p for p in DELETED_FILES]
    # Search for the deleted filenames across markdown files.
    r = subprocess.run(
        ["grep", "-rln", "--include=*.md", "-E",
         r"orchestration/provision\.py|orchestration/provision_kvm\.py|tools/orchestrator\.py",
         "."],
        cwd=REPO, capture_output=True, text=True,
    )
    for rel in r.stdout.splitlines():
        rel = rel.removeprefix("./")
        # Session logs are immutable history — always acceptable.
        if rel.startswith("docs/SessionLogs/"):
            continue
        if rel in DOC_EXCEPTIONS:
            continue
        fails.append(f"[FAIL] live doc still references a deleted path: {rel}")
    if not fails:
        print("[OK]   no live operator doc references deleted scripts")
    return fails


def check_phase7_still_passes() -> list[str]:
    r = subprocess.run(
        [str(REPO / "tools" / "verify_phase7.py")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return [f"[FAIL] verify_phase7.py regressed:\n{r.stdout}\n{r.stderr}"]
    print("[OK]   verify_phase7.py still passes")
    return []


def main() -> int:
    fails = []
    fails += check_files_deleted()
    fails += check_no_python_imports()
    fails += check_no_live_doc_refs()
    fails += check_phase7_still_passes()
    if fails:
        print()
        for f in fails:
            print(f)
        return 1
    print("\n✅  Phase 8 acceptance — all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
