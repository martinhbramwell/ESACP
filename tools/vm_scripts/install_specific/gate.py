"""gate — Decide handleBackup (first run) vs handleRestore (subsequent)."""

import subprocess
import sys
from pathlib import Path

from ._env import bench_dir


def cmd_gate():
    bd = bench_dir()
    backup_txt = Path(bd) / "BKP" / "BACKUP.txt"

    if not backup_txt.exists():
        print("=== Gate: no golden backup — running handleBackup ===")
        result = subprocess.run(
            ["bash", "BaRe/handleBackup.sh", "golden generic snapshot"],
            cwd=bd,
        )
        if result.returncode != 0:
            print(f"[FAIL] handleBackup.sh exited {result.returncode}")
            sys.exit(1)
        print("  [OK] Golden backup captured.")
        print("  Copy BKP/*.tgz to controller, then re-run with handleRestore.")
        sys.exit(0)
    else:
        tgz = backup_txt.read_text().strip()
        print(f"=== Gate: golden backup found ({tgz}) — running handleRestore ===")
        result = subprocess.run(["bash", "BaRe/handleRestore.sh"], cwd=bd)
        if result.returncode != 0:
            print(f"[FAIL] handleRestore.sh exited {result.returncode}")
            sys.exit(1)
        print("  [OK] Database restored.")
