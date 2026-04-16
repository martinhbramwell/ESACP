#!/usr/bin/env python3
"""Remove a host's wg_pubkey line from ansible/group_vars/all.yml."""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def remove_from_group_vars(
    hostname: str,
    group_vars_all: Path,
    emit: Emit,
) -> None:
    """Delete the ``wg_pubkey_<hostname>`` line from *group_vars_all*."""
    key_name = f"wg_pubkey_{hostname}"
    content = group_vars_all.read_text()
    if key_name not in content:
        emit(f"  [OK] {key_name} not in group_vars/all.yml — nothing to remove")
        return
    lines = [ln for ln in content.splitlines(keepends=True)
             if not ln.startswith(f"{key_name}")]
    group_vars_all.write_text("".join(lines))
    emit(f"  [OK] Removed {key_name} from group_vars/all.yml")
