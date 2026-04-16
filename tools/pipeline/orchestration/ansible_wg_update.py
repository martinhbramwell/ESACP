#!/usr/bin/env python3
"""Run Ansible to update hub WireGuard configuration."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def update_hub_wireguard(
    hub_key: str,
    project_root: Path,
    emit: Emit,
) -> None:
    """Run ``ansible-playbook --limit <hub> --tags wireguard``."""
    proc = subprocess.Popen(
        [
            "ansible-playbook",
            "-i", "inventory/kvm.yml",
            "site-kvm.yml",
            "--limit", hub_key,
            "--tags", "wireguard",
        ],
        cwd=str(project_root / "ansible"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for raw in proc.stdout:
        pass  # consume output — Ansible progress not useful in job logs
    proc.wait()
    if proc.returncode != 0:
        emit(f"  [WARN] Ansible wireguard update failed (exit {proc.returncode})")
    else:
        emit("  [OK] hub wg0.conf updated")
