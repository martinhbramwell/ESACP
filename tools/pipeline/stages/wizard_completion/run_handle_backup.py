"""Run handleBackup.sh on a VM and return the resulting backup filename.

Extracted from capture_backup.py so the capture flow reads as:
gate → run → rsync. Each step lives in its own unit.
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Emit


def run_handle_backup(config, emit: Emit) -> str:
    """Invoke handleBackup.sh on the VM and return the filename it produced."""
    cmd = (
        f"sudo -u {config.erp_user} bash -c"
        f" 'cd {config.bench_dir} && bash BaRe/handleBackup.sh"
        f" \"golden generic snapshot\"'"
    )
    r = ssh_run(config, cmd, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(
            f"handleBackup.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")

    r = ssh_run(config, f"cat {config.bench_dir_orig}/BKP/BACKUP.txt", timeout=10)
    if r.returncode != 0:
        raise RuntimeError("BACKUP.txt not found after handleBackup.sh")
    backup_name = r.stdout.strip()
    if not backup_name:
        raise RuntimeError("BACKUP.txt is empty after handleBackup.sh")
    emit(f"  Backup file: {backup_name}")
    return backup_name
