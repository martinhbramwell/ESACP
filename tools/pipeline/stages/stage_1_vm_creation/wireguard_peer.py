"""Unit: add WireGuard peer for the new VM (Step 1).

Runs add_peer.sh and inserts the new public key into group_vars/all.yml.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv


def add_wireguard_peer(
    hostname: str, env: KvmEnv, emit: Emit,
) -> None:
    """Generate a WireGuard keypair and register it in Ansible group_vars."""
    keys_sops = Path(env.keys_sops)
    if not keys_sops.exists():
        emit("  keys.sops.yml not found — skipping WireGuard peer generation")
        return

    dec = subprocess.run(
        ["sops", "-d", str(keys_sops)],
        cwd=env.project_root, capture_output=True, text=True,
    )
    if hostname in dec.stdout:
        emit(f"  WireGuard keys for '{hostname}' already present — skipping")
        return

    result = subprocess.run(
        ["bash", "config/wireguard/add_peer.sh", hostname],
        cwd=env.project_root, capture_output=True, text=True,
    )
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            emit(f"  {line}")
    if result.returncode != 0:
        raise RuntimeError(f"add_peer.sh failed:\n{result.stderr.strip()}")

    group_vars_all = Path(env.project_root) / "ansible" / "group_vars" / "all.yml"
    match = re.search(r'(wg_pubkey_[\w-]+):\s+"([^"]+)"', result.stdout)
    if match:
        key_name, key_value = match.group(1), match.group(2)
        content = group_vars_all.read_text()
        if key_name not in content:
            lines = content.splitlines(keepends=True)
            insert_at = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("wg_pubkey_"):
                    insert_at = i + 1
            lines.insert(insert_at, f'{key_name}: "{key_value}"\n')
            group_vars_all.write_text("".join(lines))
            emit(f"  [OK] Added {key_name} to group_vars/all.yml")
        else:
            emit(f"  [OK] {key_name} already present in group_vars/all.yml")
    else:
        emit("  [WARN] Could not parse public key from add_peer.sh output — update group_vars/all.yml manually")
