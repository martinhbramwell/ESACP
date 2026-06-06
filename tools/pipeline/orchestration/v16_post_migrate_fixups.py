"""V13->V16 post-migrate fixups primitive (ESACP#480 umbrella).

Rsyncs vm_scripts/ + runs catalogued fix/probe scripts via run_fix_script.
Each entry is idempotent + V13-safe and emits a single [PROBE] line. Add a
new #480 child by appending one FIXUPS row — no per-script function needed.

Catalogue: R1 (#486) recreate Web Page home; R3 (#498) disable orphan IRS
1099 Print Format; R8 (#617) end-to-end naming-series probe; R9 (#618)
tenant-owned Home workspace.
"""

from dataclasses import dataclass
from pathlib import Path

from tools.pipeline.orchestration.fix_script_runner import run_fix_script
from tools.pipeline.stages.common.ssh import rsync_to_vm
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


@dataclass(frozen=True)
class Fixup:
    """One post-migrate script: vm-side filename + its expected probe set."""

    label: str
    script: str            # filename under /tmp/vm_scripts/
    expected: set[str]
    changed_marker: str


FIXUPS = (
    Fixup("R1", "r1_recreate_web_page_home.py",
          {"home=present", "home=created", "homepage=absent"},
          "(was absent, now 1)"),
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
    # cwd = bench_dir/sites + bench venv so frappe imports + its relative
    # '../logs/database.log' resolve, even for scripts that only do raw SQL
    # today (prevents the venv-mismatch trap if one later adds frappe — #503).
    cmd = (f"sudo -u {config.erp_user} bash -c 'cd {config.bench_dir}/sites "
           f"&& {config.bench_dir}/env/bin/python /tmp/vm_scripts/{fx.script} "
           f"--bench-dir {config.bench_dir} --site {config.site_url}'")
    return run_fix_script(config, emit, fx.label, cmd,
                          fx.expected, fx.changed_marker)


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
