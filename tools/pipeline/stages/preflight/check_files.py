#!/usr/bin/env python3
"""Check that required files exist on the controller."""

from __future__ import annotations

import os
from pathlib import Path
from tools.pipeline.stages.common.types import Emit


def check_files(
    project_root: str,
    ssh_key_path: str,
    emit: Emit,
) -> list[tuple[Path, str, bool]]:
    """Verify age key, .sops.yaml, and SSH key pair exist.

    Returns list of (path, description, exists) tuples.
    """
    age_key = Path(os.path.expanduser("~/.config/sops/age/keys.txt"))
    sops_yaml = Path(project_root) / ".sops.yaml"
    ssh_key = Path(ssh_key_path)
    ssh_pub = Path(f"{ssh_key_path}.pub")

    file_checks = [
        (age_key,   "age decryption key"),
        (sops_yaml, "SOPS config (.sops.yaml)"),
        (ssh_key,   f"SSH private key ({ssh_key.name})"),
        (ssh_pub,   f"SSH public key ({ssh_key.name}.pub)"),
    ]

    results: list[tuple[Path, str, bool]] = []
    for path, desc in file_checks:
        exists = path.exists()
        tag = "[OK]" if exists else "[MISSING]"
        emit(f"  {tag} {desc}: {path}")
        results.append((path, desc, exists))

    return results
