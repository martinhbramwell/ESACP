"""Capture a golden backup from a VM after wizard completion.

SSH to the VM, run handleBackup.sh, SCP the resulting .tgz back
to platforms/kvm/golden_backups/ on the controller.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.orchestration.load_host_config import load_host_config
from tools.pipeline.stages.common.config import build_config
from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Emit

GOLDEN_BACKUPS = Path(__file__).resolve().parents[4] / "platforms" / "kvm" / "golden_backups"


def capture_golden_backup(
    hostname: str,
    project_root: str,
    emit: Emit,
) -> str:
    """Run handleBackup.sh on the VM and copy the result to the controller.

    Returns the backup filename (e.g. '20260414_120000-generic_iridium_blue.tgz').
    """
    host_cfg = load_host_config(hostname, project_root)
    config = build_config(hostname, host_cfg, project_root, provision_mode="generic")

    # Run handleBackup.sh on the VM
    emit("  Running handleBackup.sh on VM ...")
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

    # Read BACKUP.txt to get the filename
    r = ssh_run(
        config,
        f"cat {config.bench_dir_orig}/BKP/BACKUP.txt",
        timeout=10,
    )
    if r.returncode != 0:
        raise RuntimeError("BACKUP.txt not found after handleBackup.sh")
    backup_name = r.stdout.strip()
    if not backup_name:
        raise RuntimeError("BACKUP.txt is empty after handleBackup.sh")
    emit(f"  Backup file: {backup_name}")

    # SCP the backup to the controller
    GOLDEN_BACKUPS.mkdir(parents=True, exist_ok=True)
    local_dest = GOLDEN_BACKUPS / backup_name

    rsh = f"ssh {' '.join(config.ssh_opts)} -i {config.ssh_key}"
    r = subprocess.run(
        ["rsync", "-a", "-e", rsh,
         f"you@{config.target_ip}:{config.bench_dir_orig}/BKP/{backup_name}",
         str(local_dest)],
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        raise RuntimeError(f"rsync backup to controller failed: {r.stderr.strip()}")

    size_mb = local_dest.stat().st_size / (1024 * 1024)
    emit(f"  [OK] Golden backup saved: {local_dest.name} ({size_mb:.1f} MB)")
    return backup_name
