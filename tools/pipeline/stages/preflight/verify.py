#!/usr/bin/env python3
"""Verify preflight postconditions on this controller.

Usage: ./tools/pipeline/stages/preflight/verify.py [project_root]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_tool(name: str) -> tuple[bool, str]:
    found = shutil.which(name) is not None
    return (found, f"tool: {name}")


def check_file(path: Path, label: str) -> tuple[bool, str]:
    return (path.exists(), f"file: {label} ({path})")


def check_sops_decrypt(keys_enc: Path) -> tuple[bool, str]:
    if not keys_enc.exists():
        return (False, "sops: keys.sops.yml missing")
    r = subprocess.run(["sops", "-d", str(keys_enc)], capture_output=True, text=True)
    return (r.returncode == 0, "sops: decryption")


def verify_preflight(project_root: str) -> list[tuple[bool, str]]:
    """Run all preflight postcondition checks."""
    root = Path(project_root)
    results: list[tuple[bool, str]] = []

    # Critical tools only (representative sample)
    for tool in ("virsh", "ansible-playbook", "sops", "age"):
        results.append(check_tool(tool))

    # Required files
    age_key = Path(os.path.expanduser("~/.config/sops/age/keys.txt"))
    sops_yaml = root / ".sops.yaml"
    results.append(check_file(age_key, "age key"))
    results.append(check_file(sops_yaml, ".sops.yaml"))

    # SOPS decrypt
    keys_enc = root / "config" / "wireguard" / "keys.sops.yml"
    results.append(check_sops_decrypt(keys_enc))

    return results


def all_passed(results: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in results)


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).resolve().parents[4])

    results = verify_preflight(proj)
    print(f"\n── Preflight verification ──")
    passed = failed = 0
    for ok, msg in results:
        tag = "\u2705" if ok else "\u274c"
        print(f"  {tag}  {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
