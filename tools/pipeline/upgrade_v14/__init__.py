"""upgrade_v14 — staged ERPNext major-version upgrade orchestration.

Composes 10 stages into a single end-to-end upgrade run toward a target
major version (14, 15, 16). Each stage is `(Config, Emit) -> TaskResult`;
the orchestrator stops on the first failure (no rollback — operator reverts
via the snapshot from Stage 2). The two version-specific stages (3 switch,
10 acceptance) are built by factories so the run loop stays version-agnostic.

(Package dir name retains the `_v14` suffix as a historical artifact; the
engine is multi-version. Renaming the dir is deferred housekeeping.)
"""

from __future__ import annotations

from tools.pipeline.stages.common.types import Config, Emit

from .acceptance import make_acceptance_stage
from .bench_build import run_bench_build
from .bench_migrate import run_bench_migrate
from .bespoke_install import install_bespoke_apps
from .legacy_app_install import install_legacy_app
from .preflight import check_preflight
from .scheduler_resume import resume_scheduler
from .service_restart import restart_services
from .snapshot import take_snapshot
from .switch_branches import make_switch_stage


def build_stages(target_version: int):
    """Build the 10-stage tuple for a target major version."""
    return (
        ("1 preflight", check_preflight),
        ("2 snapshot", take_snapshot),
        (f"3 switch-to-version-{target_version}", make_switch_stage(target_version)),
        ("4 bespoke-install (#331)", install_bespoke_apps),
        ("5 install legacy_error_fixes", install_legacy_app),
        ("6 bench migrate", run_bench_migrate),
        ("7 service restart", restart_services),
        ("8 bench build", run_bench_build),
        ("9 scheduler resume", resume_scheduler),
        (f"10 acceptance (v{target_version})", make_acceptance_stage(target_version)),
    )


def run_upgrade(config: Config, emit: Emit, target_version: int) -> None:
    for label, fn in build_stages(target_version):
        emit(f"\n=== Stage {label} ===")
        result = fn(config, emit)
        emit(f"  → {result.message}")
        if not result.success:
            raise RuntimeError(f"Stage {label} failed: {result.message}")
    emit(f"\n✓ V{target_version} upgrade complete.")
