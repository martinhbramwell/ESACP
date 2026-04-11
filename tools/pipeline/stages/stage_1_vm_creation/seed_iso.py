"""Unit: build cloud-config seed ISO (Step 2).

Generates a NoCloud seed ISO containing user-data (SSH key, hostname),
network-config (static IP), and meta-data for virt-install --import.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def build_seed_iso(
    hostname: str,
    virbr0_ip: str,
    platforms_kvm: str,
    emit: Emit,
) -> Path:
    """Build a cloud-config seed ISO and return its local path."""
    controller_pubkey_path = Path.home() / ".ssh" / "hasan_mighty.pub"
    if not controller_pubkey_path.exists():
        raise FileNotFoundError(f"Controller pubkey not found: {controller_pubkey_path}")
    controller_pubkey = controller_pubkey_path.read_text().strip()

    user_data = f"""\
#cloud-config
hostname: {hostname}
fqdn: {hostname}.local
manage_etc_hosts: true

users:
  - name: you
    ssh_authorized_keys:
      - {controller_pubkey}
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: sudo, adm
    lock_passwd: true
    shell: /bin/bash
"""

    network_config = f"""\
version: 2
ethernets:
  enp1s0:
    addresses:
      - {virbr0_ip}/24
    routes:
      - to: default
        via: 192.168.122.1
    nameservers:
      addresses: [8.8.8.8, 1.1.1.1]
"""

    meta_data = f"instance-id: {hostname}\nlocal-hostname: {hostname}\n"

    work_dir = Path(tempfile.mkdtemp())
    try:
        (work_dir / "user-data").write_text(user_data)
        (work_dir / "meta-data").write_text(meta_data)
        (work_dir / "network-config").write_text(network_config)

        seed_iso = Path(platforms_kvm) / f"{hostname}-seed.iso"
        r = subprocess.run(
            [
                "cloud-localds",
                "--network-config", str(work_dir / "network-config"),
                str(seed_iso),
                str(work_dir / "user-data"),
                str(work_dir / "meta-data"),
            ],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"cloud-localds failed: {r.stderr.strip()}")
        emit(f"  [OK] Seed ISO: {seed_iso.name}")
        return seed_iso
    finally:
        shutil.rmtree(work_dir)
