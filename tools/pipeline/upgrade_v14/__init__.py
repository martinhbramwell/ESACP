"""upgrade_v14 — Phase 5 V14 upgrade orchestration.

Composes 10 stages into a single end-to-end V14 upgrade run. Each stage is
`(Config, Emit) -> TaskResult`; the orchestrator stops on the first
failure (no rollback — operator reverts via the snapshot from Stage 2).
"""

from __future__ import annotations

from tools.pipeline.stages.common.types import Config, Emit

from .acceptance import check_acceptance
from .bench_build import run_bench_build
from .bench_migrate import run_bench_migrate
from .bespoke_install import install_bespoke_apps
from .legacy_app_install import install_legacy_app
from .preflight import check_preflight
from .scheduler_resume import resume_scheduler
from .service_restart import restart_services
from .snapshot import take_snapshot
from .switch_branches import switch_to_v14

STAGES = (
    ("1 preflight", check_preflight),
    ("2 snapshot", take_snapshot),
    ("3 switch-to-v14", switch_to_v14),
    ("4 bespoke-install (#331)", install_bespoke_apps),
    ("5 install legacy_error_fixes", install_legacy_app),
    ("6 bench migrate", run_bench_migrate),
    ("7 service restart", restart_services),
    ("8 bench build", run_bench_build),
    ("9 scheduler resume", resume_scheduler),
    ("10 acceptance", check_acceptance),
)


def run_upgrade_v14(config: Config, emit: Emit) -> None:
    for label, fn in STAGES:
        emit(f"\n=== Stage {label} ===")
        result = fn(config, emit)
        emit(f"  → {result.message}")
        if not result.success:
            raise RuntimeError(f"Stage {label} failed: {result.message}")
    emit("\n✓ V14 upgrade complete.")
