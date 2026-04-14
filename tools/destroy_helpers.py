#!/usr/bin/env python3
"""Destroy pipeline helpers — extracted from api.py for use by job_worker.py.

These functions handle the multi-step VM teardown:
WG peer removal → VM destroy → hosts_map cleanup → group_vars cleanup →
inventory regen → Ansible WG update → SOPS key removal → cloud-init cleanup.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

import yaml


Emit = Callable[[str], None]


def get_wg_pubkey(
    hostname: str,
    keys_sops: Path,
    project_root: Path,
) -> str | None:
    """Decrypt keys.sops.yml and return the WireGuard public key for hostname."""
    if not keys_sops.exists():
        return None
    dec = subprocess.run(
        ["sops", "-d", str(keys_sops)],
        cwd=project_root, capture_output=True, text=True,
    )
    if dec.returncode != 0:
        return None
    keys_data = yaml.safe_load(dec.stdout)
    peer = keys_data.get(hostname, {})
    return peer.get("public_key") if isinstance(peer, dict) else None


def remove_wg_peer_live(
    hostname: str,
    pubkey: str,
    hosts_map: Path,
    emit: Emit,
) -> None:
    """Remove the WireGuard peer from the hub live (wg set ... remove)."""
    with open(hosts_map) as f:
        data = yaml.safe_load(f)
    kvm = data["groups"].get("kvm", {})
    hub = next((h for h in kvm.values() if h.get("wg_role") == "hub"), None)
    if not hub:
        emit("  [WARN] Cannot find hub in hosts_map.yml — skipping live WG removal")
        return
    hub_ip = hub["virbr0_ip"]
    hub_hv = hub["hypervisor"]
    r = subprocess.run(
        ["ssh", "-o", f"ProxyJump={hub_hv}", "-o", "StrictHostKeyChecking=no",
         f"you@{hub_ip}", f"sudo wg set wg0 peer {pubkey} remove"],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        emit(f"  [WARN] wg set peer remove failed: {r.stderr.strip()}")
    else:
        emit(f"  [OK] Live WireGuard peer for {hostname} removed from hub")


def destroy_vm(
    hostname: str,
    host_cfg: dict,
    emit: Emit,
) -> None:
    """Destroy (stop) then undefine (delete + storage) the VM on its hypervisor."""
    hypervisor = host_cfg.get("hypervisor")
    if not hypervisor:
        raise RuntimeError(f"No hypervisor configured for '{hostname}'")

    for _attempt in range(20):
        snap_r = subprocess.run(
            ["ssh", hypervisor,
             f"virsh --connect qemu:///system snapshot-list {hostname} --name"],
            capture_output=True, text=True, timeout=30,
        )
        snapshots = [s.strip() for s in snap_r.stdout.strip().splitlines() if s.strip()]
        if not snapshots:
            break
        for snap_name in snapshots:
            del_r = subprocess.run(
                ["ssh", hypervisor,
                 f"virsh --connect qemu:///system snapshot-delete {hostname} '{snap_name}'"],
                capture_output=True, text=True, timeout=60,
            )
            if del_r.returncode == 0:
                emit(f"  [OK] Deleted snapshot: {snap_name}")
            else:
                emit(f"  [WARN] snapshot-delete {snap_name}: {del_r.stderr.strip()}")

    for virsh_cmd in (
        f"virsh --connect qemu:///system destroy {hostname}",
        f"virsh --connect qemu:///system undefine {hostname} --remove-all-storage",
    ):
        r = subprocess.run(
            ["ssh", hypervisor, virsh_cmd],
            capture_output=True, text=True, timeout=60,
        )
        combined = (r.stdout + r.stderr).lower()
        if r.returncode != 0:
            if "domain is not running" in combined or "failed to get domain" in combined:
                emit(f"  [OK] {virsh_cmd} — VM was already stopped or absent, continuing")
            else:
                raise RuntimeError(f"'{virsh_cmd}' failed: {r.stderr.strip()}")
        else:
            emit(f"  [OK] {virsh_cmd}")


def remove_from_hosts_map(
    hostname: str,
    hosts_map: Path,
    emit: Emit,
) -> None:
    """Remove the host YAML block from hosts_map.yml using regex."""
    text = hosts_map.read_text()
    pattern = rf'\n    {re.escape(hostname)}:\n(?:[ ]{{6}}[^\n]*\n)+'
    new_text = re.sub(pattern, "\n", text)
    new_text = re.sub(r'\n{3,}', "\n\n", new_text)
    if new_text == text:
        emit(f"  [WARN] '{hostname}' block not found in hosts_map.yml — nothing removed")
    else:
        hosts_map.write_text(new_text)
        emit(f"  [OK] Removed '{hostname}' from hosts_map.yml")


def remove_from_group_vars_all(
    hostname: str,
    group_vars_all: Path,
    emit: Emit,
) -> None:
    """Remove the wg_pubkey_<hostname> line from group_vars/all.yml."""
    key_name = f"wg_pubkey_{hostname}"
    content = group_vars_all.read_text()
    if key_name not in content:
        emit(f"  [OK] {key_name} not in group_vars/all.yml — nothing to remove")
        return
    lines = [l for l in content.splitlines(keepends=True) if not l.startswith(f"{key_name}")]
    group_vars_all.write_text("".join(lines))
    emit(f"  [OK] Removed {key_name} from group_vars/all.yml")


def remove_keys_from_sops(
    hostname: str,
    keys_sops: Path,
    project_root: Path,
    emit: Emit,
) -> None:
    """Decrypt keys.sops.yml, remove hostname entries, re-encrypt in place."""
    if not keys_sops.exists():
        emit("  [WARN] keys.sops.yml not found — skipping")
        return

    sops_conf = project_root / ".sops.yaml"
    match = re.search(r'age1[a-z0-9]+', sops_conf.read_text())
    if not match:
        raise RuntimeError(f"Cannot find age recipient in {sops_conf}")
    age_recipient = match.group(0)

    dec = subprocess.run(
        ["sops", "-d", str(keys_sops)],
        cwd=project_root, capture_output=True, text=True,
    )
    if dec.returncode != 0:
        raise RuntimeError(f"sops decrypt failed: {dec.stderr.strip()}")

    keys_data = yaml.safe_load(dec.stdout)
    removed = []

    if hostname in keys_data:
        del keys_data[hostname]
        removed.append(hostname)

    psks = keys_data.get("preshared_keys", {})
    for k in [k for k in psks if hostname in k]:
        del psks[k]
        removed.append(f"preshared_keys.{k}")

    if not removed:
        emit(f"  [WARN] No keys for '{hostname}' found in keys.sops.yml")
        return

    work_dir = Path(tempfile.mkdtemp())
    try:
        plain = work_dir / "keys.sops.yml"
        plain.write_text(yaml.dump(keys_data, default_flow_style=False, sort_keys=False))

        enc = subprocess.run(
            ["sops", "--encrypt", "--age", age_recipient,
             "--input-type", "yaml", "--output-type", "yaml", str(plain)],
            capture_output=True, text=True,
        )
        if enc.returncode != 0:
            raise RuntimeError(f"sops encrypt failed: {enc.stderr.strip()}")
        keys_sops.write_text(enc.stdout)
        emit(f"  [OK] Removed from keys.sops.yml: {', '.join(removed)}")
    finally:
        for f in work_dir.iterdir():
            subprocess.run(["shred", "-u", str(f)], capture_output=True)
        work_dir.rmdir()
