"""Seed ISO upload helpers for VM builds.

ISO generation is handled by tools.pipeline.stages.stage_1_vm_creation.seed_iso.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv


def upload_seed_to_pool(seed_local: Path, vm: str, emit: Emit) -> None:
    """Upload seed ISO into the local default libvirt pool via virsh."""
    iso_name = f"{vm}-seed.iso"
    size = seed_local.stat().st_size
    subprocess.run(["virsh", "vol-delete", iso_name, "--pool", "default"], capture_output=True)
    r = subprocess.run(
        ["virsh", "vol-create-as", "default", iso_name, str(size), "--format", "raw"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"vol-create-as failed: {r.stderr.strip()}")
    r = subprocess.run(
        ["virsh", "vol-upload", "--pool", "default", iso_name, str(seed_local)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"vol-upload failed: {r.stderr.strip()}")
    emit(f"  {iso_name} uploaded to default pool")


def upload_seed_to_hypervisor(
    seed_local: Path, vm: str, env: KvmEnv, emit: Emit,
) -> str:
    """SCP seed ISO to remote hypervisor. Returns remote path."""
    remote_seed = f"{env.images_dir}/{vm}-seed.iso"
    r = subprocess.run(
        ["scp", str(seed_local), f"{env.hypervisor_user}@{env.hypervisor_alias}:{remote_seed}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"scp seed ISO failed: {r.stderr.strip()}")
    emit(f"  Seed ISO uploaded to {env.hypervisor_alias}")
    return remote_seed
