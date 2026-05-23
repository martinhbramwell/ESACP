"""Substrate-apply primitive — apply a bespoke-app migration on a lab VM.

Bundles the institutional protections (g1 patch-log preseed + g2 fixture
Custom Field clear) around the `bench migrate` call so that LSKB#15-style
substrate-apply workflows cannot bypass them. See ESACP#418.

Sequence:
  1. Rsync `tools/vm_scripts/` → `/tmp/vm_scripts/` on the target VM
     (mirrors Stage-4 config_bundle.py:72; idempotent).
  2. Run `g1_seed_patch_log.py` (skips already-applied patches that would
     re-run and crash against the restored DB — prevents ESACP#398 class).
  3. Run `g2_clear_fixture_custom_fields.py` (clears fixture-defined Custom
     Fields + colliding DocField rows — prevents `forma_de_pago_preferida`
     and similar ce_sri#10-class collisions).
  4. Run `bench migrate` as ERP_USER.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.ssh import rsync_to_vm, ssh_run
from tools.pipeline.stages.common.types import Config, Emit, TaskResult


def _run_step(config: Config, emit: Emit, label: str, cmd: str, *, timeout: int = 600) -> bool:
    r = ssh_run(config, cmd, timeout=timeout)
    if r.returncode == 0:
        emit(f"  [OK] {label}")
        return True
    emit(f"  [FAIL] {label}: rc={r.returncode}")
    if r.stdout.strip():
        emit(f"    stdout: {r.stdout.strip()[-500:]}")
    if r.stderr.strip():
        emit(f"    stderr: {r.stderr.strip()[-500:]}")
    return False


def apply_substrate_migration(config: Config, emit: Emit) -> TaskResult:
    """Run g1 + g2 + bench migrate over SSH. Returns TaskResult."""
    project = Path(config.project_root)
    local_vm_scripts = str(project / "tools" / "vm_scripts") + "/"

    emit(f"  rsync vm_scripts → {config.hostname}:/tmp/vm_scripts/")
    r = rsync_to_vm(config, local_vm_scripts, "/tmp/vm_scripts/", timeout=60)
    if r.returncode != 0:
        return TaskResult(False, False, f"rsync vm_scripts: {r.stderr.strip()}")

    g1 = (f"python3 /tmp/vm_scripts/g1_seed_patch_log.py "
          f"--bench-dir {config.bench_dir} --site {config.site_url}")
    if not _run_step(config, emit, "g1_seed_patch_log", g1):
        return TaskResult(False, False, "g1_seed_patch_log failed")

    g2 = (f"python3 /tmp/vm_scripts/g2_clear_fixture_custom_fields.py "
          f"--bench-dir {config.bench_dir} --site {config.site_url}")
    if not _run_step(config, emit, "g2_clear_fixture_custom_fields", g2):
        return TaskResult(False, False, "g2_clear_fixture_custom_fields failed")

    migrate = (f"sudo -u {config.erp_user} bash -c "
               f"'cd {config.bench_dir} && bench --site {config.site_url} migrate'")
    if not _run_step(config, emit, "bench migrate", migrate, timeout=1800):
        return TaskResult(False, False, "bench migrate failed")

    return TaskResult(True, True, "substrate migration applied")
