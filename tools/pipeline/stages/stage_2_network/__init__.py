"""Stage 2: Network — saconsole WG hub, Cloudflare DNS, TLS cert, WG spoke.

Orchestrates Steps 8–9 of the provision pipeline.  Extracted from
``_run_provision_erpnext`` in api.py.
"""

from __future__ import annotations

from tools.pipeline.stages.common.types import Config, Emit

from .cloudflare_dns import upsert_cloudflare_dns
from .saconsole_wg_hub import update_saconsole_wg_hub
from .tls_cert import ensure_tls_cert
from .wireguard_spoke import configure_wireguard_spoke


def run_stage_2(config: Config, emit: Emit) -> None:
    """Execute network setup (Steps 8–9).

    Parameters
    ----------
    config : Config
        Immutable per-VM configuration (hostname, wg_ip, project_root, etc.).
    emit : Emit
        Log callback.

    Raises
    ------
    RuntimeError
        If any critical step fails.
    """
    # ── Step 8: Update saconsole WireGuard hub ──
    emit("── Step 8: Update saconsole WireGuard (Ansible) ──")
    r = update_saconsole_wg_hub(config, emit)
    if not r.success:
        emit(f"  [WARN] {r.message}")
    else:
        emit(f"  [OK] {r.message}")

    # ── Step 8b: Cloudflare DNS A record ──
    emit("── Step 8b: Cloudflare DNS A record ──")
    r = upsert_cloudflare_dns(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    # ── Step 8c: Distribute TLS cert from saconsole to VM ──
    emit("── Step 8c: Distribute TLS wildcard cert to VM ──")
    r = ensure_tls_cert(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    # ── Step 9: Configure WireGuard spoke on new VM ──
    emit("── Step 9: Configure WireGuard spoke (Ansible) ──")
    r = configure_wireguard_spoke(config, emit)
    if not r.success:
        emit(f"  [WARN] {r.message}")
    else:
        emit(f"  [OK] {r.message}")
