#!/usr/bin/env python3
"""Remove a WireGuard peer from the hub's live wg0 interface."""

from __future__ import annotations

import subprocess

from tools.pipeline.stages.common.types import Emit


def remove_wg_peer_live(
    hostname: str,
    pubkey: str,
    hub_ip: str,
    hub_hypervisor: str,
    emit: Emit,
) -> None:
    """SSH to the hub and ``wg set wg0 peer <pubkey> remove``."""
    r = subprocess.run(
        ["ssh", "-o", f"ProxyJump={hub_hypervisor}",
         "-o", "StrictHostKeyChecking=no",
         f"you@{hub_ip}", f"sudo wg set wg0 peer {pubkey} remove"],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        emit(f"  [WARN] wg set peer remove failed: {r.stderr.strip()}")
    else:
        emit(f"  [OK] Live WireGuard peer for {hostname} removed from hub")
