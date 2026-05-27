"""V13->V16 post-migrate fixups primitive (ESACP#480 umbrella).

Rsyncs vm_scripts/ + runs catalogued fix-scripts (R1 #486, R3 #498) via
the run_fix_script helper. Each script is idempotent + V13-safe.
"""

from pathlib import Path

from tools.pipeline.orchestration.fix_script_runner import run_fix_script
from tools.pipeline.stages.common.ssh import rsync_to_vm
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

R1_SCRIPT = "/tmp/vm_scripts/r1_recreate_web_page_home.py"
R1_EXPECTED = {"home=present", "home=created", "homepage=absent"}
R1_CHANGED_MARKER = "(was absent, now 1)"

R3_SCRIPT = "/tmp/vm_scripts/r3_disable_irs_1099_pf.py"
R3_EXPECTED = {"disabled=1", "disabled=absent"}
R3_CHANGED_MARKER = "(was 0, now 1)"


def _rsync_scripts(config: Config, emit: Emit) -> TaskResult:
    project = Path(config.project_root)
    local = str(project / "tools" / "vm_scripts") + "/"
    emit(f"  rsync vm_scripts -> {config.hostname}:/tmp/vm_scripts/")
    r = rsync_to_vm(config, local, "/tmp/vm_scripts/", timeout=60)
    if r.returncode != 0:
        return TaskResult(False, False, f"rsync vm_scripts: {r.stderr.strip()}")
    return TaskResult(True, False, "vm_scripts rsynced")


def _run_r1(config: Config, emit: Emit) -> TaskResult:
    # cwd = bench_dir/sites so frappe's RotatingFileHandler can resolve
    # its relative '../logs/database.log' to bench_dir/logs/ (#486).
    cmd = (f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir}/sites "
           f"&& {config.bench_dir}/env/bin/python {R1_SCRIPT} "
           f"--bench-dir {config.bench_dir} --site {config.site_url}'")
    return run_fix_script(config, emit, "R1", cmd,
                          R1_EXPECTED, R1_CHANGED_MARKER)


def _run_r3(config: Config, emit: Emit) -> TaskResult:
    cmd = (f"python3 {R3_SCRIPT} --bench-dir {config.bench_dir} "
           f"--site {config.site_url}")
    return run_fix_script(config, emit, "R3", cmd,
                          R3_EXPECTED, R3_CHANGED_MARKER)


def apply_v16_post_migrate_fixups(config: Config, emit: Emit) -> TaskResult:
    """Apply all V13->V16 post-migrate fixups to the target VM."""
    sync = _rsync_scripts(config, emit)
    if not sync.success:
        return sync
    results = []
    for runner in (_run_r1, _run_r3):
        r = runner(config, emit)
        if not r.success:
            return r
        results.append(r)
    msg = "; ".join(r.message for r in results)
    return TaskResult(True, any(r.changed for r in results),
                      f"V16 post-migrate fixups applied: {msg}")
