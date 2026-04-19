"""Rsync database backup (BACKUP.txt + named archive) to target VM."""

from __future__ import annotations

from tools.bespoke_root import BESPOKE_ROOT
from tools.pipeline.stages.common.ssh import rsync_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

BKP_SRC = BESPOKE_ROOT / "ce_sri" / "BKP"


def _backup_present(config: Config) -> bool:
    r = ssh_run(config,
                f"test -f {config.bench_dir_orig}/BKP/BACKUP.txt && echo y",
                timeout=10)
    return r.returncode == 0 and "y" in r.stdout


def ensure_backup(config: Config, emit: Emit) -> TaskResult:
    """Rsync BKP directory (BACKUP.txt + named file) to the VM."""
    if _backup_present(config):
        return TaskResult(True, False, "Backup already on VM")

    backup_txt = BKP_SRC / "BACKUP.txt"
    if not BKP_SRC.exists() or not backup_txt.exists():
        return TaskResult(True, False, f"BKP source not found — skipping")

    active_file = backup_txt.read_text().strip()
    active_path = BKP_SRC / active_file
    if not active_path.exists():
        return TaskResult(False, False,
                          f"BACKUP.txt names '{active_file}' but file missing")

    size_mb = active_path.stat().st_size / (1024 * 1024)
    date_part = active_file[:8]
    date_str = f"{date_part[:4]}/{date_part[4:6]}/{date_part[6:8]}"
    emit(f"  Copying backup of {date_str} (~{size_mb:.0f}MB)")

    r = rsync_to_vm(
        config,
        f"{BKP_SRC}/",
        f"{config.bench_dir_orig}/BKP/",
        timeout=600,
        extra_args=[
            "--rsync-path=sudo rsync",
            "--include", "BACKUP.txt",
            "--include", active_file,
            "--exclude", "*",
        ],
    )
    if r.returncode != 0:
        return TaskResult(False, False,
                          f"rsync BKP failed: {r.stderr.strip()}")
    return TaskResult(True, True,
                      f"BKP ({active_file}) → {config.bench_dir_orig}/BKP")
