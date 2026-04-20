#!/usr/bin/env python3
"""Remove a host's YAML block from hosts_map.yml."""

from __future__ import annotations

import re
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def remove_from_hosts_map(
    hostname: str,
    hosts_map: Path,
    emit: Emit,
) -> None:
    """Delete the indented block for *hostname* from *hosts_map*."""
    text = hosts_map.read_text()
    pattern = rf'\n    {re.escape(hostname)}:\n(?:[ ]{{6}}[^\n]*\n)+'
    new_text = re.sub(pattern, "", text)
    new_text = re.sub(r'\n{3,}', "\n\n", new_text)
    if new_text == text:
        emit(f"  [WARN] '{hostname}' block not found in hosts_map.yml — nothing removed")
    else:
        hosts_map.write_text(new_text)
        emit(f"  [OK] Removed '{hostname}' from hosts_map.yml")
