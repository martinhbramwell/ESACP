#!/usr/bin/env python3
"""Look up a host's WireGuard public key from the SOPS-encrypted keyring."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


def get_wg_pubkey(
    hostname: str,
    keys_sops: Path,
    project_root: Path,
) -> str | None:
    """Decrypt keys.sops.yml and return the WireGuard public key for *hostname*.

    Returns ``None`` if the file is missing, decryption fails, or the host
    has no entry.
    """
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
