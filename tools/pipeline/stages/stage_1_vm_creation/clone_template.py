"""Unit: clone template qcow2 on hypervisor (Step 4)."""

from __future__ import annotations

import json
import subprocess

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv


def clone_template(
    hostname: str, env: KvmEnv, emit: Emit,
) -> str:
    """vol-clone the Packer-built template image.  Returns the template name."""
    meta_r = subprocess.run(
        ["ssh", env.hypervisor_alias,
         f"cat {env.metadata_dir}/erpnext-v13-latest.json 2>/dev/null"],
        capture_output=True, text=True, timeout=10,
    )
    if meta_r.returncode != 0 or not meta_r.stdout.strip():
        raise RuntimeError("Template metadata not found on hypervisor — run a Packer build first")

    meta = json.loads(meta_r.stdout)
    template_image = meta.get("image")
    if not template_image:
        raise RuntimeError("Template metadata missing 'image' field")
    emit(f"  Template image: {template_image}")

    clone_r = subprocess.run(
        ["ssh", env.hypervisor_alias,
         f"virsh --connect qemu:///system vol-clone --pool {env.pool} "
         f"'{template_image}' '{hostname}.qcow2'"],
        capture_output=True, text=True, timeout=300,
    )
    if clone_r.returncode != 0:
        raise RuntimeError(f"vol-clone failed: {clone_r.stderr.strip()}")
    emit(f"  [OK] Cloned {template_image} → {hostname}.qcow2")
    return template_image
