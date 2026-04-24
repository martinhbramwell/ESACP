"""Capture a golden backup from a VM after wizard completion.

Three-step flow: bench-layer gate → run handleBackup.sh → rsync the
.tgz to platforms/kvm/golden_backups/ on the controller. Each step
lives in its own unit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.orchestration.load_host_config import load_host_config
from tools.pipeline.stages.common.config import build_config
from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.wizard_completion.clean_bench_gate import (
    assert_clean_bench,
)
from tools.pipeline.stages.wizard_completion.run_handle_backup import (
    run_handle_backup,
)

GOLDEN_BACKUPS = Path(__file__).resolve().parents[4] / "platforms" / "kvm" / "golden_backups"


def capture_golden_backup(
    hostname: str,
    project_root: str,
    emit: Emit,
) -> str:
    """Gate, run, stage. Returns backup filename."""
    host_cfg = load_host_config(hostname, project_root)
    config = build_config(hostname, host_cfg, project_root, provision_mode="generic")

    emit("  Verifying clean-bench substrate before capture ...")
    assert_clean_bench(config, emit)

    emit("  Running handleBackup.sh on VM ...")
    backup_name = run_handle_backup(config, emit)

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
