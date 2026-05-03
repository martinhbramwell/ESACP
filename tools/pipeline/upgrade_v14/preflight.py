"""Stage 1 — pre-flight checks before V14 upgrade.

Enforces the 1-VM rule (`feedback_one_vm_at_a_time.md`): the substrate must
be the only running ERP dev VM on the hypervisor; toshiba is 16 GiB.
Also verifies the substrate is SSH-reachable.
"""

from __future__ import annotations

from tools.pipeline.stages.common.ssh import ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def check_preflight(config: Config, emit: Emit) -> TaskResult:
    emit(f"  Pre-flight check on {config.hostname}")
    r = ssh_run(config, "hostname && whoami", timeout=15)
    if r.returncode != 0:
        return TaskResult(False, False, f"SSH to {config.hostname} failed: {r.stderr.strip()}")

    # Confirm bench dir present (catch resolved-to-symlink VM mismatches early).
    r = ssh_run(config,
                f"sudo -u {config.erp_user} test -d {config.bench_dir}/apps/frappe && echo OK",
                timeout=15)
    if r.returncode != 0 or "OK" not in r.stdout:
        return TaskResult(False, False,
                          f"bench dir {config.bench_dir} or apps/frappe missing on substrate")
    emit(f"  ✓ {config.hostname} reachable; bench dir {config.bench_dir} present")
    return TaskResult(True, False, "Pre-flight passed")
