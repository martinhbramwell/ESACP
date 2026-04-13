"""Unit: wait for VM to become SSH-ready (Step 6)."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from tools.pipeline.stages.common.types import Emit


def wait_for_ssh(
    hostname: str,
    virbr0_ip: str,
    hypervisor_alias: str,
    ssh_key: str,
    emit: Emit,
    *,
    max_attempts: int = 60,
    interval: int = 10,
) -> None:
    """Poll SSH on the VM until it responds or timeout."""
    # Clear stale host keys
    subprocess.run(["ssh-keygen", "-R", virbr0_ip], capture_output=True)
    subprocess.run(["ssh-keygen", "-R", hostname], capture_output=True)

    target_ssh = [
        "ssh",
        "-o", f"ProxyJump={hypervisor_alias}",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        "-i", ssh_key,
        f"you@{virbr0_ip}",
    ]

    for attempt in range(max_attempts):
        time.sleep(interval)
        r = subprocess.run(
            target_ssh + ["echo ready"],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and "ready" in r.stdout:
            emit(f"  [OK] SSH up after ~{(attempt + 1) * interval}s")
            return
        if attempt % 3 == 0:
            emit(f"  Waiting for SSH ... ({(attempt + 1) * interval}s)")

    raise RuntimeError(f"VM did not become SSH-ready within {max_attempts * interval // 60} minutes")
