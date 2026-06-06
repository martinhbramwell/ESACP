"""Macro: provision a generic ERPNext VM (stages 1-9, no production data)."""

from __future__ import annotations

import subprocess

from tools.pipeline.orchestration.load_host_config import load_host_config, target_frappe_major  # noqa: E501
from tools.pipeline.stages.common.config import build_config
from tools.pipeline.stages.common.log_format import stage_banner
from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv
from tools.pipeline.stages.stage_1_vm_creation import run_stage_1
from tools.pipeline.stages.stage_2_network import run_stage_2
from tools.pipeline.stages.stage_3_connectivity import run_stage_3
from tools.pipeline.stages.stage_4_content_delivery import run_stage_4
from tools.pipeline.stages.stage_5_tls import run_stage_5
from tools.pipeline.stages.stage_6_base_platform import run_stage_6
from tools.pipeline.stages.stage_7_data_restoration import run_stage_7
from tools.pipeline.stages.stage_8_app_config import run_stage_8
from tools.pipeline.stages.stage_9_service_activation import run_stage_9


def run(
    hostname: str,
    virbr0_ip: str,
    project_root: str,
    emit: Emit,
    *,
    cleanup_cfg: dict | None = None,
) -> None:
    """Provision a generic ERPNext VM (stages 1-9, provision_mode=generic).

    Stages 3/7/8/9 skip restore-specific units (backup restore,
    ce_sri secrets, Social Login). The result is a blank ERPNext
    with the setup wizard ready on first browser visit.

    Raises RuntimeError on the first stage that fails.
    """
    # ── Stage 1: VM Creation ──
    emit(stage_banner("Stage 1: VM Creation"))
    kvm_env = KvmEnv.from_project_root(project_root)
    run_stage_1(
        hostname=hostname,
        virbr0_ip=virbr0_ip,
        env=kvm_env,
        emit=emit,
        cleanup_cfg=cleanup_cfg,
        target_major=target_frappe_major(load_host_config(hostname, project_root)),
    )

    # Build Config for stages 2-9 with generic mode
    host_cfg = load_host_config(hostname, project_root)
    config = build_config(
        hostname, host_cfg, project_root, provision_mode="generic",
    )

    # ── Stages 2-9 ──
    _STAGES: list[tuple[str, object]] = [
        ("Stage 2: Network",            run_stage_2),
        ("Stage 3: Connectivity",       run_stage_3),
        ("Stage 4: Content Delivery",   run_stage_4),
        ("Stage 5: TLS",                run_stage_5),
        ("Stage 6: Base Platform",      run_stage_6),
        ("Stage 7: Data Init",          run_stage_7),
        ("Stage 8: App Config",         run_stage_8),
        ("Stage 9: Service Activation", run_stage_9),
    ]
    for label, stage_fn in _STAGES:
        emit(stage_banner(label))
        stage_fn(config, emit)

    # ── Final snapshot ──
    emit(stage_banner("Final snapshot"))
    _take_final_snapshot(hostname, kvm_env.hypervisor_alias, emit)


def _take_final_snapshot(
    hostname: str, hypervisor: str, emit: Emit,
) -> None:
    """Take the post-provision snapshot on the hypervisor."""
    snap_name = "ERPNext v13 Generic Baseline"
    r = subprocess.run(
        [
            "ssh", hypervisor,
            f"virsh --connect qemu:///system snapshot-create-as"
            f" {hostname} '{snap_name}' --atomic",
        ],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        emit(f"  [WARN] Snapshot failed: {r.stderr.strip()}")
    else:
        emit(f"  [OK] Snapshot '{snap_name}' taken")
