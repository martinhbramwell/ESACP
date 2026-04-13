"""Unit: upload seed ISO to hypervisor (Step 3)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv


def upload_seed_iso(
    hostname: str, seed_local: Path, env: KvmEnv, emit: Emit,
) -> str:
    """SCP the seed ISO to the hypervisor.  Returns the remote path."""
    remote_seed = f"{env.images_dir}/{hostname}-seed.iso"
    r = subprocess.run(
        ["scp", str(seed_local),
         f"{env.hypervisor_user}@{env.hypervisor_alias}:{remote_seed}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"scp seed ISO failed: {r.stderr.strip()}")
    emit(f"  [OK] Seed ISO at {env.hypervisor_alias}:{remote_seed}")
    return remote_seed
