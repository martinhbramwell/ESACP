#!/usr/bin/env python3
"""Standalone test orchestrator: destroy + rebuild a VM using Stage 1.

Usage:
    ./tools/orchestrator.py dev03

Destroys the VM on its hypervisor, then runs Stage 1 (VM Creation)
to rebuild it from the Packer template.  Stops after the Baseline
snapshot — no differentiation.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.pipeline.orchestration.destroy_vm import destroy_vm
from tools.pipeline.orchestration.load_host_config import load_host_config
from tools.pipeline.stages.env_kvm import KvmEnv
from tools.pipeline.stages.stage_1_vm_creation import run_stage_1


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

    # Phase 2: Stage 1 — VM Creation
    _emit(f"── Rebuilding {hostname} via Stage 1 ──")
    env = KvmEnv.from_project_root(PROJECT_ROOT)
    run_stage_1(
        hostname=hostname,
        virbr0_ip=virbr0_ip,
        env=env,
        emit=_emit,
    )
    _emit(f"=== Done — {hostname} rebuilt, Baseline snapshot taken ===")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <hostname>")
        sys.exit(1)
    main(sys.argv[1])
