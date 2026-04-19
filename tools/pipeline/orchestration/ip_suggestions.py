#!/usr/bin/env python3
"""Derive suggested next-available IPs + default hypervisor for a new KVM host.

Pure function over a hosts_map.yml kvm-group dict. Shared by the
``GET /api/hosts`` route (surfaces suggestions to the UI form) and
the ``./tools/esacp.py addHost`` CLI dispatcher.
"""

from __future__ import annotations

from tools.host_identity import DEFAULT_HYPERVISOR, virbr0_subnet_prefix


def _last_octet(ip: str) -> int:
    try:
        return int(ip.split(".")[-1])
    except (ValueError, IndexError):
        return 0


def suggest_next_ips(kvm_hosts: dict) -> dict[str, str]:
    """Return next-free ``wg_ip``, ``virbr0_ip`` and default ``hypervisor``."""
    wg_octets   = [_last_octet(h["wg_ip"])     for h in kvm_hosts.values() if h.get("wg_ip")]
    vbr_octets  = [_last_octet(h["virbr0_ip"]) for h in kvm_hosts.values() if h.get("virbr0_ip")]
    hypervisors = [h.get("hypervisor") for h in kvm_hosts.values() if h.get("hypervisor")]
    default_hv  = (max(set(hypervisors), key=hypervisors.count)
                   if hypervisors else DEFAULT_HYPERVISOR)
    return {
        "wg_ip":      f"10.10.0.{max(wg_octets, default=0) + 1}",
        "virbr0_ip":  f"{virbr0_subnet_prefix()}.{max(vbr_octets, default=9) + 1}",
        "hypervisor": default_hv,
    }
