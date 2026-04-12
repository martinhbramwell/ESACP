#!/usr/bin/env python3
"""Standalone test orchestrator: destroy + rebuild a VM through Stages 1–2.

Usage:
    ./tools/orchestrator.py dev03

Destroys the VM on its hypervisor, then runs Stage 1 (VM Creation)
and Stage 2 (Network).  Verifies postconditions after each stage —
a verify failure after running is a hard error.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.pipeline.orchestration.destroy_vm import destroy_vm
from tools.pipeline.orchestration.load_host_config import load_host_config
from tools.pipeline.stages.common.config import build_config
from tools.pipeline.stages.env_kvm import KvmEnv
from tools.pipeline.stages.stage_1_vm_creation import run_stage_1
from tools.pipeline.stages.stage_1_vm_creation.verify import (
    all_passed as s1_all_passed,
    verify_stage_1,
)
from tools.pipeline.stages.stage_2_network import run_stage_2
from tools.pipeline.stages.stage_2_network.verify import (
    all_passed as s2_all_passed,
    verify_stage_2,
)


def _emit(line: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {line}", flush=True)


def main(hostname: str) -> None:
    _emit(f"=== Orchestrator: destroy + rebuild {hostname} ===")

    # Load host config from hosts_map.yml
    host_cfg = load_host_config(hostname, PROJECT_ROOT)
    hypervisor = host_cfg.get("hypervisor")
    virbr0_ip = host_cfg.get("virbr0_ip")
    if not virbr0_ip:
        raise RuntimeError(f"No virbr0_ip for '{hostname}' in hosts_map.yml")

    # Phase 1: Destroy
    _emit(f"── Destroying {hostname} on {hypervisor} ──")
    destroy_vm(hostname, hypervisor, _emit)
    _emit(f"  [OK] {hostname} destroyed")

    env = KvmEnv.from_project_root(PROJECT_ROOT)
    hypervisor_alias = env.hypervisor_alias

    # Phase 2: Stage 1 — VM Creation
    _emit(f"── Rebuilding {hostname} via Stage 1 ──")
    run_stage_1(
        hostname=hostname,
        virbr0_ip=virbr0_ip,
        env=env,
        emit=_emit,
    )

    # Verify Stage 1 postconditions
    s1_results = verify_stage_1(
        hostname=hostname, virbr0_ip=virbr0_ip,
        hypervisor=hypervisor_alias, project_root=str(PROJECT_ROOT),
    )
    if not s1_all_passed(s1_results):
        failures = [msg for ok, msg in s1_results if not ok]
        raise RuntimeError(f"Stage 1 verify failed: {'; '.join(failures)}")
    _emit("  [OK] Stage 1 verified")

    # Phase 3: Stage 2 — Network
    _emit(f"── Networking {hostname} via Stage 2 ──")
    cfg = build_config(hostname, host_cfg, str(PROJECT_ROOT))
    run_stage_2(cfg, _emit)

    # Verify Stage 2 postconditions
    s2_results = verify_stage_2(
        hostname=hostname, wg_ip=host_cfg["wg_ip"],
        virbr0_ip=virbr0_ip, hypervisor=hypervisor_alias,
        project_root=str(PROJECT_ROOT),
    )
    if not s2_all_passed(s2_results):
        failures = [msg for ok, msg in s2_results if not ok]
        raise RuntimeError(f"Stage 2 verify failed: {'; '.join(failures)}")
    _emit("  [OK] Stage 2 verified")

    _emit(f"=== Done — {hostname} rebuilt through Stage 2 ===")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <hostname>")
        sys.exit(1)
    main(sys.argv[1])
