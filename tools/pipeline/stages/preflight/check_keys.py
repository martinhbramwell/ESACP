#!/usr/bin/env python3
"""Validate SOPS/age decryption and WireGuard key structure."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tools.pipeline.stages.common.types import Emit, TaskResult

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def check_keys(
    project_root: str, expected_hosts: list[str], hub_name: str, emit: Emit,
) -> TaskResult:
    """Decrypt keys.sops.yml and verify WG key structure."""
    age_key = Path(os.path.expanduser("~/.config/sops/age/keys.txt"))
    sops_yml = Path(project_root) / ".sops.yaml"
    keys_enc = Path(project_root) / "config" / "wireguard" / "keys.sops.yml"

    # --- file existence ---
    missing: list[str] = []
    for path, label in [
        (age_key, "age key"), (sops_yml, ".sops.yaml"), (keys_enc, "keys.sops.yml"),
    ]:
        if path.exists():
            emit(f"  [OK] {label}: {path}")
        else:
            emit(f"  [MISSING] {label}: {path}")
            missing.append(str(path))
    if missing:
        return TaskResult(False, False, f"Missing files: {', '.join(missing)}")

    # --- SOPS decryption ---
    emit("  Attempting SOPS decryption...")
    result = subprocess.run(
        ["sops", "-d", str(keys_enc)], capture_output=True, text=True,
    )
    if result.returncode != 0:
        return TaskResult(False, False, f"SOPS decryption failed: {result.stderr.strip()}")

    if yaml is None:
        return TaskResult(False, False, "PyYAML not installed")
    try:
        decrypted = yaml.safe_load(result.stdout)
    except yaml.YAMLError as exc:
        return TaskResult(False, False, f"YAML parse error: {exc}")

    # --- per-host key pairs ---
    ok = True
    for host in expected_hosts:
        block = decrypted.get(host, {})
        has_priv = "private_key" in block
        has_pub = "public_key" in block
        tag = "[OK]" if (has_priv and has_pub) else "[MISSING]"
        emit(f"  {tag} {host}: private_key + public_key")
        if not (has_priv and has_pub):
            ok = False

    # --- preshared keys ---
    psks = decrypted.get("preshared_keys", {})
    for spoke in (h for h in expected_hosts if h != hub_name):
        psk_key = f"{spoke}_{hub_name}"
        tag = "[OK]" if psk_key in psks else "[MISSING]"
        emit(f"  {tag} preshared_key: {psk_key}")
        if psk_key not in psks:
            ok = False

    msg = ("All WireGuard keys present and decryptable"
           if ok else "Key structure incomplete")
    return TaskResult(ok, False, msg)
