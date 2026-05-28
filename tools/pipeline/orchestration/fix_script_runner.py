"""Run a fix-script over SSH and parse its [PROBE] / changed-marker output.

Shared protocol for post-migrate fixup primitives (e.g.
v16_post_migrate_fixups). Each fix-script must emit a single
`  [PROBE] <key>=<value>` line that matches one of the expected probes,
and a `(was ..., now ...)` marker on the success-with-mutation path.
"""

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult

PROBE_PREFIX = "  [PROBE] "


def run_fix_script(config: Config, emit: Emit, label: str, cmd: str,
                   expected: set[str], changed_marker: str) -> TaskResult:
    """Run *cmd* over SSH, parse [PROBE] line, detect changed_marker."""
    r = ssh_run(config, cmd, timeout=120)
    if r.returncode != 0:
        emit(f"  [FAIL] {label}: rc={r.returncode}")
        for stream, txt in (("stdout", r.stdout), ("stderr", r.stderr)):
            if txt.strip():
                emit(f"    {stream}: {txt.strip()[-500:]}")
        return TaskResult(False, False, f"{label} failed")
    probe, changed = None, False
    for line in r.stdout.splitlines():
        emit(line)
        if line.startswith(PROBE_PREFIX):
            probe = line[len(PROBE_PREFIX):].strip()
        if changed_marker in line:
            changed = True
    if probe not in expected:
        return TaskResult(False, False, f"{label} probe unexpected: {probe!r}")
    return TaskResult(True, changed, f"{label} probe={probe}")
