"""V13->V16 post-migrate fixups primitive (ESACP#498, #480 child).

Rsyncs `tools/vm_scripts/` and runs each catalogued fix-script over SSH.
Catalogue today: R3 disable IRS 1099 PF. Caller runs this AFTER bench
migrate to V16; running against a V13 substrate is benign.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import rsync_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

R3_SCRIPT = "/tmp/vm_scripts/r3_disable_irs_1099_pf.py"
R3_PROBE_PREFIX = "  [PROBE] "
R3_EXPECTED_PROBES = {"disabled=1", "disabled=absent"}


def _rsync_scripts(config: Config, emit: Emit) -> TaskResult:
    project = Path(config.project_root)
    local = str(project / "tools" / "vm_scripts") + "/"
    emit(f"  rsync vm_scripts -> {config.hostname}:/tmp/vm_scripts/")
    r = rsync_to_vm(config, local, "/tmp/vm_scripts/", timeout=60)
    if r.returncode != 0:
        return TaskResult(False, False, f"rsync vm_scripts: {r.stderr.strip()}")
    return TaskResult(True, False, "vm_scripts rsynced")


def _run_r3(config: Config, emit: Emit) -> TaskResult:
    cmd = (f"python3 {R3_SCRIPT} "
           f"--bench-dir {config.bench_dir} --site {config.site_url}")
    r = ssh_run(config, cmd, timeout=60)
    if r.returncode != 0:
        emit(f"  [FAIL] R3: rc={r.returncode}")
        if r.stdout.strip():
            emit(f"    stdout: {r.stdout.strip()[-500:]}")
        if r.stderr.strip():
            emit(f"    stderr: {r.stderr.strip()[-500:]}")
        return TaskResult(False, False, "R3 disable IRS 1099 PF failed")

    probe = None
    changed = False
    for line in r.stdout.splitlines():
        emit(line)
        if line.startswith(R3_PROBE_PREFIX):
            probe = line[len(R3_PROBE_PREFIX):].strip()
        if "(was 0, now 1)" in line:
            changed = True

    if probe not in R3_EXPECTED_PROBES:
        return TaskResult(False, False, f"R3 probe unexpected: {probe!r}")

    return TaskResult(True, changed, f"R3 probe={probe}")


def apply_v16_post_migrate_fixups(config: Config, emit: Emit) -> TaskResult:
    """Apply all V13->V16 post-migrate fixups to the target VM."""
    sync = _rsync_scripts(config, emit)
    if not sync.success:
        return sync

    r3 = _run_r3(config, emit)
    if not r3.success:
        return r3

    any_changed = r3.changed
    return TaskResult(True, any_changed,
                      f"V16 post-migrate fixups applied: {r3.message}")
