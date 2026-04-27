"""Clear stale SSH known_hosts entries for a host.

Used by destroy (after VM teardown — host keys guaranteed stale) and by
host_registration (defense-in-depth — in case destroy was bypassed or was
performed on a different controller).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def clear_known_hosts(keys: list[str], emit: Emit) -> None:
    """Remove ~/.ssh/known_hosts entries for each given key (hostname or IP).

    Idempotent: succeeds whether entries exist or not. Each key is passed
    to `ssh-keygen -R` independently; missing entries are silently skipped.
    """
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    if not known_hosts.exists():
        emit("  [SKIP] ~/.ssh/known_hosts does not exist")
        return

    cleared = []
    for key in keys:
        if not key:
            continue
        r = subprocess.run(
            ["ssh-keygen", "-f", str(known_hosts), "-R", key],
            capture_output=True, text=True, timeout=10,
        )
        output = (r.stdout or "") + (r.stderr or "")
        if "found: line" in output:
            cleared.append(key)

    if cleared:
        emit(f"  [OK] cleared known_hosts entries: {', '.join(cleared)}")
    else:
        emit("  [SKIP] no stale known_hosts entries to clear")
