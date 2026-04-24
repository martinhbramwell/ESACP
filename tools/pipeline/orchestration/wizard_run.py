"""Playwright wizard completion — record, replay, or restore-existing."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from tools.pipeline.orchestration import snapshot_ops
from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv
from tools.pipeline.stages.wizard_completion.capture_backup import (
    capture_golden_backup,
)
from tools.pipeline.stages.wizard_completion.restore_backup import (
    restore_golden_backup,
)


def run_wizard(
    mode: str, hostname: str, site_url: str, arg: str,
    project_root: Path, emit: Emit,
) -> None:
    """Dispatch to record/replay/existing. Unknown modes emit a warning."""
    if mode == "record":
        _record(hostname, site_url, project_root, emit)
        capture_golden_backup(hostname, str(project_root), emit)
    elif mode == "replay":
        _replay(hostname, site_url, arg, project_root, emit)
        capture_golden_backup(hostname, str(project_root), emit)
        hypervisor = KvmEnv.from_project_root(project_root).hypervisor_alias
        snapshot_ops.create_snapshot(
            hostname, "ERPNext V13 Complete Generic", emit, hypervisor=hypervisor,
        )
    elif mode == "existing":
        emit(f"── Restoring from golden backup: {arg} ──")
        restore_golden_backup(hostname, arg, str(project_root), emit)
        emit("  [OK] Golden backup restored")
    else:
        emit(f"  [WARN] Unknown wizard_mode '{mode}' — skipping wizard")


def _record(hostname: str, site_url: str, root: Path, emit: Emit) -> None:
    emit(f"── Wizard ready — recording browser at {site_url} ──")
    emit("  Close the browser when wizard is complete.")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = root / "prototypes" / "cytoscape" / "recordings" / "wizard" / f"{hostname}-{ts}.spec.js"
    output.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["node", str(root / "prototypes" / "cytoscape" / "recordings" / "record_wizard.js"),
         "--url", site_url, "--output", str(output)],
        cwd=str(root / "prototypes" / "cytoscape"), timeout=2400,
    )
    if r.returncode != 0:
        emit(f"  [WARN] Recorder exited with code {r.returncode}")
    else:
        emit(f"  [OK] Recording saved: {output.name}")


def _replay(
    hostname: str, site_url: str, script_name: str, root: Path, emit: Emit,
) -> None:
    emit(f"── Replaying wizard recording: {script_name} ──")
    script = root / "prototypes" / "cytoscape" / "recordings" / "wizard" / script_name
    if not script.exists():
        raise RuntimeError(f"Recording not found: {script}")
    r = subprocess.run(
        ["node", str(root / "prototypes" / "cytoscape" / "recordings" / "replay_wizard.js"),
         "--script", str(script), "--url", site_url],
        cwd=str(root / "prototypes" / "cytoscape"), timeout=600,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Replay failed (exit {r.returncode})")
    emit("  [OK] Wizard replay complete")
