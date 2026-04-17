"""CLI: create or list KVM VM snapshots.

Note: this module contains a direct ``subprocess.run`` call to
``platforms/kvm/snapshot.py`` — this is a documented Phase 7 exception
tracked in GitHub issue #206, pending extraction to a pipeline primitive.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.cli._common import banner

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOT_PY  = PROJECT_ROOT / "platforms" / "kvm" / "snapshot.py"


def run(args, config: dict) -> int:
    vm   = args.vm
    name = args.name

    if name:
        banner(f"Snapshot: {vm} / {name}")
        r = subprocess.run(["python3", str(SNAPSHOT_PY), "create", vm, name])
    else:
        banner(f"Snapshots: {vm}")
        r = subprocess.run(["python3", str(SNAPSHOT_PY), "list", vm])
    return r.returncode
