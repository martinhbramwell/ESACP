#!/usr/bin/env python3
"""Remove a host's WireGuard keys from the SOPS-encrypted keyring."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import yaml

from tools.pipeline.stages.common.types import Emit


def remove_keys_from_sops(
    hostname: str,
    keys_sops: Path,
    project_root: Path,
    emit: Emit,
) -> None:
    """Decrypt keys.sops.yml, remove *hostname* entries, re-encrypt in place."""
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
        plain.write_text(yaml.dump(keys_data, default_flow_style=False,
                                   sort_keys=False))
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
