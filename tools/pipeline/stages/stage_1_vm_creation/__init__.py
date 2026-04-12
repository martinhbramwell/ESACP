"""Stage 1: VM Creation — WG peer, seed ISO, vol-clone, virt-install, wait SSH, snapshot.

Orchestrates Steps 0–7 of the provision pipeline.  Extracted from
``_run_provision_erpnext`` in api.py.
"""

from __future__ import annotations

from pathlib import Path

from tools.pipeline.stages.common.types import Emit
from tools.pipeline.stages.env_kvm import KvmEnv

from .baseline_snapshot import take_baseline_snapshot
from .verify import all_passed, verify_stage_1
from .cleanup_residue import cleanup_residue
from .clone_template import clone_template
from .seed_iso import build_seed_iso
from .upload_seed import upload_seed_iso
from .virt_install import virt_install_import
from .wait_ssh import wait_for_ssh
from .wireguard_peer import add_wireguard_peer


def run_stage_1(
    hostname: str,
    virbr0_ip: str,
    env: KvmEnv,
    emit: Emit,
    *,
    ssh_key: str | None = None,
    cleanup_cfg: dict | None = None,
) -> None:
    """Execute VM creation (Steps 0–7).

    Parameters
    ----------
    hostname : str
        VM hostname (e.g. ``dev02``).
    virbr0_ip : str
        Static IP on the virbr0 bridge network.
    env : KvmEnv
        KVM environment context (hypervisor alias, pool, paths).
    emit : Emit
        Log callback.
    ssh_key : str, optional
        Path to controller SSH private key.  Defaults to ``~/.ssh/hasan_mighty``.
    cleanup_cfg : dict, optional
        If set, destroy leftover VM residue before building (Step 0).
    """
    if ssh_key is None:
        ssh_key = str(Path.home() / ".ssh" / "hasan_mighty")

    # ── Idempotency gate: skip if all postconditions already met ──
    results = verify_stage_1(
        hostname=hostname,
        virbr0_ip=virbr0_ip,
        hypervisor=env.hypervisor_alias,
        project_root=env.project_root,
        ssh_key=ssh_key,
    )
    if all_passed(results):
        emit("[OK] Stage 1 already satisfied — skipping")
        return

    # ── Step 0: Clean up residue from a previous build ──
    if cleanup_cfg:
        emit("── Step 0: Cleaning up residue from previous build ──")
        cleanup_residue(hostname, cleanup_cfg, env.hypervisor_alias, emit)
        emit("  [OK] Old VM residue removed — starting fresh")

    # ── Step 1: WireGuard peer ──
    emit("── Step 1: Add WireGuard peer ──")
    add_wireguard_peer(hostname, env, emit)

    # ── Step 2: Build seed ISO ──
    emit("── Step 2: Build cloud-config seed ISO ──")
    seed_local = build_seed_iso(hostname, virbr0_ip, env.platforms_kvm, emit)

    # ── Step 3: Upload seed ISO to hypervisor ──
    emit("── Step 3: Upload seed ISO to hypervisor ──")
    remote_seed = upload_seed_iso(hostname, seed_local, env, emit)

    # ── Step 4: Clone template qcow2 ──
    emit("── Step 4: Clone template qcow2 ──")
    clone_template(hostname, env, emit)

    # ── Step 5: virt-install --import ──
    emit("── Step 5: virt-install --import ──")
    virt_install_import(hostname, remote_seed, env, emit)

    # ── Step 6: Wait for SSH ──
    emit("── Step 6: Wait for SSH ──")
    wait_for_ssh(hostname, virbr0_ip, env.hypervisor_alias, ssh_key, emit)

    # ── Step 7: Take Baseline snapshot ──
    emit("── Step 7: Take Baseline snapshot ──")
    take_baseline_snapshot(hostname, env.hypervisor_alias, emit)
