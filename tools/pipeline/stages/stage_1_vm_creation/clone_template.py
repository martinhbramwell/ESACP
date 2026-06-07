"""Unit: clone template qcow2 on hypervisor (Step 4)."""

from __future__ import annotations

import json
import subprocess

from tools.pipeline.orchestration.template_metadata import (
    DEFAULT_MAJOR, metadata_basename,
)
from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv


def clone_template(
    hostname: str, env: KvmEnv, emit: Emit, major: int = DEFAULT_MAJOR,
) -> str:
    """vol-clone the Packer-built template image for *major*.

    Selects the per-major template metadata (``erpnext-v{major}-latest.json``)
    so a v15 host clones the v15 template and a v13 host the v13 one
    (dual-template; ESACP #631).  Returns the template image name.
    """
    meta_file = f"{env.metadata_dir}/{metadata_basename(major)}"
    emit(f"  Template line: v{major} ({metadata_basename(major)})")
    meta_r = subprocess.run(
        ["ssh", env.hypervisor_alias, f"cat {meta_file} 2>/dev/null"],
        capture_output=True, text=True, timeout=10,
    )
    if meta_r.returncode != 0 or not meta_r.stdout.strip():
        raise RuntimeError(
            f"v{major} template metadata not found on hypervisor "
            f"({meta_file}) — run a Packer build for that line first")

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
