#!/usr/bin/env python3
"""Regenerate ansible/inventory/kvm.yml from hosts_map.yml."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def regenerate_inventory(project_root: Path, emit: Emit) -> None:
    """Run ``generate_inventory.py`` and raise on failure."""
    result = subprocess.run(
        [str(project_root / "tools" / "generate_inventory.py")],
        cwd=project_root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"generate_inventory.py failed:\n{result.stderr}")
    emit("  [OK] inventory regenerated")
