"""Stage 2: Network — hub WG config, Cloudflare DNS, TLS cert, WG spoke.

Orchestrates Steps 8–9 of the provision pipeline.  Extracted from
``_run_provision_erpnext`` in api.py.
"""

from __future__ import annotations

from tools.pipeline.stages.common.log_format import step_header
from tools.pipeline.stages.common.types import Config, Emit

from .cloudflare_dns import upsert_cloudflare_dns
from .verify import all_passed, verify_stage_2
from .saconsole_wg_hub import update_hub_wg
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
    # ── Idempotency gate: skip if all postconditions already met ──
    results = verify_stage_2(
        hostname=config.hostname,
        wg_ip=config.wg_ip,
        virbr0_ip=config.virbr0_ip,
        hypervisor=config.hypervisor or "toshiba",
        project_root=config.project_root,
        ssh_key=config.ssh_key,
    )
    if all_passed(results):
        emit("[OK] Stage 2 already satisfied — skipping")
        return

    # ── Update hub WireGuard ──
    emit(step_header("Update hub WireGuard (Ansible)"))
    r = update_hub_wg(config, emit)
    if not r.success:
        emit(f"  [WARN] {r.message}")
    else:
        emit(f"  [OK] {r.message}")

    # ── Cloudflare DNS A record ──
    emit(step_header("Cloudflare DNS A record"))
    r = upsert_cloudflare_dns(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    # ── Distribute TLS cert from hub to VM ──
    emit(step_header("Distribute TLS wildcard cert to VM"))
    r = ensure_tls_cert(config, emit)
    if not r.success:
        raise RuntimeError(r.message)
    tag = "[CHANGED]" if r.changed else "[OK]"
    emit(f"  {tag} {r.message}")

    # ── Configure WireGuard spoke on new VM ──
    emit(step_header("Configure WireGuard spoke (Ansible)"))
    r = configure_wireguard_spoke(config, emit)
    if not r.success:
        emit(f"  [WARN] {r.message}")
    else:
        emit(f"  [OK] {r.message}")
