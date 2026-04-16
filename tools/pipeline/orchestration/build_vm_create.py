"""virt-install commands for local and remote autoinstall builds."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv


def create_vm_local(
    vm: str, project_root: str, ram: int, emit: Emit,
) -> None:
    """Run virt-install with autoinstall on the local hypervisor."""
    images_dir = Path("/var/lib/libvirt/images")
    iso_symlink = Path(project_root) / "ubuntu-24.04.4-live-server-amd64.iso"
    try:
        r = subprocess.run(
            ["readlink", "-f", str(iso_symlink)],
            capture_output=True, text=True, check=True,
        )
        iso_real = r.stdout.strip()
    except subprocess.CalledProcessError:
        iso_real = str(iso_symlink)

    if not Path(iso_real).exists():
        raise RuntimeError(f"ISO not found: {iso_real}")

    seed = images_dir / f"{vm}-seed.iso"
    disk = images_dir / f"{vm}.qcow2"
    cmd = [
        "virt-install",
        "--name", vm, "--ram", str(ram), "--vcpus", "2",
        "--disk", f"path={disk},size=20,format=qcow2",
        "--location", f"{iso_real},kernel=casper/vmlinuz,initrd=casper/initrd",
        "--disk", f"path={seed},device=cdrom,readonly=on",
        "--network", "network=default",
        "--os-variant", "ubuntu24.04",
        "--extra-args", "autoinstall ds=nocloud",
        "--graphics", "vnc", "--noautoconsole",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"virt-install failed: {r.stderr.strip()}")
    emit(f"  {vm} created, autoinstall in progress")


def create_vm_remote(
    vm: str, ram: int, env: KvmEnv, seed_path: str, emit: Emit,
) -> None:
    """Run virt-install with autoinstall on a remote hypervisor via SSH."""
    ubuntu_iso = f"{env.images_dir}/ubuntu-24.04.4-live-server-amd64.iso"
    virt_cmd = (
        f"virt-install --connect qemu:///system"
        f" --name {vm} --ram {ram} --vcpus 2"
        f" --disk pool={env.pool},size=20,format=qcow2"
        f" --location '{ubuntu_iso},kernel=casper/vmlinuz,initrd=casper/initrd'"
        f" --disk path={seed_path},device=cdrom,readonly=on"
        f" --network network=default --os-variant ubuntu20.04"
        f" --extra-args 'autoinstall ds=nocloud'"
        f" --graphics vnc --noautoconsole"
    )
    r = subprocess.run(
        ["ssh", env.hypervisor_alias, virt_cmd],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"virt-install on {env.hypervisor_alias} failed: {r.stderr.strip()}")
    emit(f"  {vm} created on {env.hypervisor_alias}, autoinstall in progress")
