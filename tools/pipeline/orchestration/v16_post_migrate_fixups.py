"""V13->V16 post-migrate fixups primitive (ESACP#480 umbrella).

Rsyncs vm_scripts/ + runs catalogued fix-scripts via run_fix_script. Each
fixup carries `min_version` (the major it applies from); the leg runs only
fixups with `min_version <= target` — cumulative. V15 leg: #626 server-scripts,
R3 print-format, R8 naming-series probe; V16 adds R1 homepage. R8 is an
end-to-end PROBE (one draft Sales Invoice/run → always `changed`). Add a fixup
by appending one FIXUPS row — no new function needed.
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
    min_version: int     # applies from this major version onward (15, 16, ...)


# Dependency-ordered (docstring): #626 before R8; R1 is V16-only.
FIXUPS = (
    Fixup("#626", "server_scripts_enable_626.py",
          {"server_scripts=enabled"}, ", now 1)", 15),
    Fixup("R3", "r3_disable_irs_1099_pf.py",
          {"disabled=1", "disabled=absent"}, "(was 0, now 1)", 15),
    Fixup("R8", "r8_naming_series_probe.py",
          {"naming_series=ok"}, "(series advanced)", 15),
    Fixup("R1", "r1_recreate_web_page_home.py",
          {"home=present", "home=created", "homepage=absent"}, "(was absent, now 1)", 16),
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


def apply_v16_post_migrate_fixups(config: Config, emit: Emit,
                                  target_version: int = 16) -> TaskResult:
    """Apply fixups with ``min_version <= target_version`` (cumulative).

    Default 16 preserves the V13->V16 CLI behaviour (run all); the upgrade
    leg passes its own target (e.g. 15) to run only that leg's fixups.
    """
    sync = _rsync_scripts(config, emit)
    if not sync.success:
        return sync
    results = []
    for fx in (f for f in FIXUPS if f.min_version <= target_version):
        r = _run_fixup(config, emit, fx)
        if not r.success:
            return r
        results.append(r)
    msg = "; ".join(r.message for r in results)
    return TaskResult(True, any(r.changed for r in results),
                      f"post-migrate fixups (v{target_version}) applied: {msg}")
