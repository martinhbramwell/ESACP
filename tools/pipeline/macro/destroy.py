#!/usr/bin/env python3
"""Macro: full destroy — 9-step teardown.

Steps: live WG peer → VM → hosts_map → group_vars → inventory → hub WG
→ SOPS keys → cloud-init → known_hosts cleanup.
"""

from __future__ import annotations

from pathlib import Path

from tools.host_identity import HUB_HYPERVISOR, HUB_KEY, HUB_VIRBR0_IP
from tools.pipeline.orchestration.ansible_wg_update import update_hub_wireguard
from tools.pipeline.orchestration.cloud_init_cleanup import remove_cloud_init
from tools.pipeline.orchestration.destroy_vm import destroy_vm
from tools.pipeline.orchestration.group_vars_remove import remove_from_group_vars
from tools.pipeline.orchestration.hosts_map_remove import remove_from_hosts_map
from tools.pipeline.orchestration.inventory_regen import regenerate_inventory
from tools.pipeline.orchestration.known_hosts_cleanup import clear_known_hosts
from tools.pipeline.orchestration.sops_key_remove import remove_keys_from_sops
from tools.pipeline.orchestration.wg_peer_remove import remove_wg_peer_live
from tools.pipeline.orchestration.wg_pubkey import get_wg_pubkey
from tools.pipeline.stages.common.types import Emit


def run(
    hostname: str,
    host_cfg: dict,
    project_root: str,
    emit: Emit,
) -> None:
    """Execute the full destroy sequence for *hostname*.

    *host_cfg* is the host's dict from hosts_map.yml (must include
    ``hypervisor``).  Raises ``RuntimeError`` on unrecoverable failures.
    """
    root = Path(project_root)
    hypervisor = host_cfg.get("hypervisor", "")
    keys_sops = root / "config" / "wireguard" / "keys.sops.yml"

    emit("── Step 1: Remove live WireGuard peer ──")
    pubkey = get_wg_pubkey(hostname, keys_sops, root)
    if pubkey:
        remove_wg_peer_live(hostname, pubkey, HUB_VIRBR0_IP, HUB_HYPERVISOR, emit)
    else:
        emit(f"  [WARN] No pubkey found for {hostname} — skipping live WG removal")

    emit("── Step 2: Destroy VM ──")
    destroy_vm(hostname, hypervisor, emit)

    emit("── Step 3: Update hosts_map.yml ──")
    remove_from_hosts_map(hostname, root / "hosts_map.yml", emit)

    emit("── Step 4: Update group_vars/all.yml ──")
    remove_from_group_vars(hostname, root / "ansible" / "group_vars" / "all.yml", emit)

    emit("── Step 5: Regenerate inventory ──")
    regenerate_inventory(root, emit)

    emit("── Step 6: Update hub WireGuard config (Ansible) ──")
    update_hub_wireguard(HUB_KEY, root, emit)

    emit("── Step 7: Remove WireGuard keys ──")
    remove_keys_from_sops(hostname, keys_sops, root, emit)

    emit("── Step 8: Remove cloud-init directory ──")
    remove_cloud_init(hostname, root / "platforms" / "kvm" / "cloud-init", emit)

    emit("── Step 9: Clear stale ~/.ssh/known_hosts entries ──")
    clear_known_hosts(
        [hostname, host_cfg.get("wg_ip") or "", host_cfg.get("virbr0_ip") or ""],
        emit,
    )

    emit("── Destroy complete ──")
