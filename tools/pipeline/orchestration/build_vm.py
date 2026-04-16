"""Orchestrator: build a VM from scratch via autoinstall (remote or local)."""

from __future__ import annotations

import time
from pathlib import Path

from tools.host_identity import HUB_KEY
from tools.pipeline.stages.common.known_hosts import (
    known_hosts_entries, populate_known_hosts, populate_known_hosts_via_hypervisor,
    remove_known_hosts,
)
from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv

from .build_vm_create import create_vm_local, create_vm_remote
from .build_vm_poll import ensure_running_and_ssh
from .build_vm_seed import build_seed_iso, upload_seed_to_hypervisor, upload_seed_to_pool
from .hypervisor_helpers import ansible_ping, vm_exists


def build_vm(
    vm: str, vm_info: dict, project_root: str, ssh_key: str, emit: Emit,
) -> None:
    """Build *vm* via autoinstall. Raises RuntimeError on failure."""
    env = KvmEnv.from_project_root(project_root)
    hypervisor = vm_info.get("hypervisor")
    virbr0_ip = vm_info.get("virbr0_ip", "")
    ram = 4096 if vm == HUB_KEY else 2048

    # ── Steps 1–2: Seed ISO + VM creation (idempotent) ──
    if vm_exists(vm, hypervisor):
        emit("  VM already exists — skipping seed ISO + creation")
    else:
        seed = build_seed_iso(vm, env.platforms_kvm, emit)
        if hypervisor:
            remote_seed = upload_seed_to_hypervisor(seed, vm, env, emit)
            create_vm_remote(vm, ram, env, remote_seed, emit)
        else:
            _ensure_seed_in_pool(seed, vm, emit)
            create_vm_local(vm, project_root, ram, emit)

    # ── Step 3: Clear stale known_hosts ──
    entries = known_hosts_entries(vm_info)
    remove_known_hosts(entries, emit)

    # ── Step 4: Poll for SSH or autoinstall poweroff ──
    if not virbr0_ip:
        raise RuntimeError("No virbr0_ip in host config — cannot poll")
    ensure_running_and_ssh(vm, virbr0_ip, hypervisor, env.hypervisor_user, emit)

    # ── Update known_hosts with fresh key ──
    remove_known_hosts(entries, emit)
    if hypervisor:
        populate_known_hosts_via_hypervisor(virbr0_ip, hypervisor, emit)
    else:
        populate_known_hosts([virbr0_ip] if virbr0_ip else [vm], emit)

    # ── Ansible ping confirmation ──
    for attempt in range(6):
        if ansible_ping(vm, project_root, ssh_key):
            emit("  Ansible connectivity confirmed")
            return
        time.sleep(5)
    raise RuntimeError(f"Ansible cannot reach {vm} — check SSH user/key")


def _ensure_seed_in_pool(seed: Path, vm: str, emit: Emit) -> None:
    """Upload seed to local pool only if not already present."""
    dest = Path("/var/lib/libvirt/images") / f"{vm}-seed.iso"
    if dest.exists():
        emit(f"  {dest} already present — skipping upload")
    else:
        upload_seed_to_pool(seed, vm, emit)
