"""Unit: virt-install --import to start the VM (Step 5)."""

from __future__ import annotations

import subprocess

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv


def virt_install_import(
    hostname: str, remote_seed: str, env: KvmEnv, emit: Emit,
) -> None:
    """Boot the VM from the cloned template + seed ISO."""
    virt_cmd = (
        f"virt-install --connect qemu:///system"
        f" --name {hostname}"
        f" --ram 4096"
        f" --vcpus 2"
        f" --disk vol={env.pool}/{hostname}.qcow2"
        f" --disk path={remote_seed},device=cdrom,readonly=on"
        f" --network network=default"
        f" --os-variant ubuntu20.04"
        f" --import"
        f" --graphics vnc"
        f" --noautoconsole"
    )
    r = subprocess.run(
        ["ssh", env.hypervisor_alias, virt_cmd],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f"virt-install --import failed: {r.stderr.strip()}")
    emit(f"  [OK] VM {hostname} started (booting from template)")
