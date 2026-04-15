"""Restore a golden backup onto a VM.

Rsync the named .tgz from platforms/kvm/golden_backups/ to the VM,
write BACKUP.txt, then run handleRestore.sh.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.orchestration.load_host_config import load_host_config
from tools.pipeline.stages.common.config import build_config
from tools.pipeline.stages.common.ssh import rsync_to_vm, ssh_run
from tools.pipeline.stages.common.types import Emit

GOLDEN_BACKUPS = Path(__file__).resolve().parents[4] / "platforms" / "kvm" / "golden_backups"


def restore_golden_backup(
    hostname: str,
    backup_name: str,
    project_root: str,
    emit: Emit,
) -> None:
    """Rsync a golden backup to the VM and run handleRestore.sh."""
    local_path = GOLDEN_BACKUPS / backup_name
    if not local_path.exists():
        raise RuntimeError(f"Golden backup not found: {local_path}")

    host_cfg = load_host_config(hostname, project_root)
    config = build_config(hostname, host_cfg, project_root, provision_mode="generic")

    bkp_dir = f"{config.bench_dir_orig}/BKP"

    # Ensure BKP directory exists on VM
    ssh_run(config, f"sudo -u {config.erp_user} mkdir -p {bkp_dir}", timeout=10)

    # Rsync the .tgz to the VM
    size_mb = local_path.stat().st_size / (1024 * 1024)
    emit(f"  Copying {backup_name} ({size_mb:.1f} MB) to VM ...")
    r = rsync_to_vm(
        config,
        str(local_path),
        f"{bkp_dir}/",
        timeout=600,
        extra_args=["--rsync-path=sudo rsync"],
    )
    if r.returncode != 0:
        raise RuntimeError(f"rsync backup to VM failed: {r.stderr.strip()}")

    # Write BACKUP.txt
    r = ssh_run(
        config,
        f"echo '{backup_name}' | sudo -u {config.erp_user} tee {bkp_dir}/BACKUP.txt",
        timeout=10,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Failed to write BACKUP.txt: {r.stderr.strip()}")
    emit(f"  [OK] BACKUP.txt → {backup_name}")

    # Run handleRestore.sh
    emit("  Running handleRestore.sh ...")
    cmd = (
        f"sudo -u {config.erp_user} bash -c"
        f" 'cd {config.bench_dir} && DEFER_SOCIAL_LOGIN=1"
        f" bash BaRe/handleRestore.sh'"
    )
    r = ssh_run(config, cmd, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(
            f"handleRestore.sh failed (exit {r.returncode}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    for line in r.stdout.strip().splitlines():
        emit(f"  {line}")
    emit("  [OK] Golden backup restored")
