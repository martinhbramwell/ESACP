"""V13->V16 post-migrate fixups primitive (ESACP#480 umbrella).

Rsyncs vm_scripts/ + runs catalogued fix-scripts (R1 #486, R3 #498, R8 #617)
via run_fix_script. R1/R3 are idempotent fixes; R8 is an end-to-end naming-
series PROBE (creates one draft Sales Invoice per run, so it always reports
`changed`). All V13-safe. Add a fixup by appending one FIXUPS row — no new
function needed.
"""

from pathlib import Path
from typing import NamedTuple

from tools.pipeline.orchestration.fix_script_runner import run_fix_script
from tools.pipeline.stages.common.ssh import rsync_to_vm
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


class Fixup(NamedTuple):
    """One post-migrate script: vm-side filename + its expected probe set."""
    label: str
    script: str          # filename under /tmp/vm_scripts/
    expected: set        # acceptable [PROBE] values; anything else => fail
    changed_marker: str  # substring of output => this run changed state


FIXUPS = (
    Fixup("R1", "r1_recreate_web_page_home.py",
          {"home=present", "home=created", "homepage=absent"}, "(was absent, now 1)"),
    Fixup("R3", "r3_disable_irs_1099_pf.py",
          {"disabled=1", "disabled=absent"}, "(was 0, now 1)"),
    Fixup("R8", "r8_naming_series_probe.py",
          {"naming_series=ok"}, "(series advanced)"),
)


def _rsync_scripts(config: Config, emit: Emit) -> TaskResult:
    project = Path(config.project_root)
    local = str(project / "tools" / "vm_scripts") + "/"
    emit(f"  rsync vm_scripts -> {config.hostname}:/tmp/vm_scripts/")
    r = rsync_to_vm(config, local, "/tmp/vm_scripts/", timeout=60)
    if r.returncode != 0:
        return TaskResult(False, False, f"rsync vm_scripts: {r.stderr.strip()}")
    return TaskResult(True, False, "vm_scripts rsynced")


def _run_fixup(config: Config, emit: Emit, fx: Fixup) -> TaskResult:
    # Uniform invocation (#503): bench venv + sudo + cwd at sites/. R1 and R8
    # use the frappe API and need the venv; R3 only does raw mysql today, but
    # the uniform shape prevents the silent venv-mismatch trap if a script
    # later adds Frappe imports.
    cmd = (f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir}/sites "
           f"&& {config.bench_dir}/env/bin/python /tmp/vm_scripts/{fx.script} "
           f"--bench-dir {config.bench_dir} --site {config.site_url}'")
    return run_fix_script(config, emit, fx.label, cmd, fx.expected, fx.changed_marker)


def apply_v16_post_migrate_fixups(config: Config, emit: Emit) -> TaskResult:
    """Apply all V13->V16 post-migrate fixups to the target VM."""
    sync = _rsync_scripts(config, emit)
    if not sync.success:
        return sync
    results = []
    for fx in FIXUPS:
        r = _run_fixup(config, emit, fx)
        if not r.success:
            return r
        results.append(r)
    msg = "; ".join(r.message for r in results)
    return TaskResult(True, any(r.changed for r in results),
                      f"V16 post-migrate fixups applied: {msg}")
