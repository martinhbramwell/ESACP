#!/usr/bin/env python3
"""Remove a host's cloud-init directory."""

from __future__ import annotations

import shutil
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def remove_cloud_init(hostname: str, cloud_init_dir: Path, emit: Emit) -> None:
    """Delete ``<cloud_init_dir>/<hostname>/`` if it exists."""
    ci_dir = cloud_init_dir / hostname
    if ci_dir.exists():
        shutil.rmtree(ci_dir)
        emit(f"  [OK] Removed cloud-init dir {ci_dir}")
