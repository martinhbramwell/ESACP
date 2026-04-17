"""Build a single /api/hosts response row — extracted to keep hosts.py small."""

from __future__ import annotations

from tools.host_identity import ZONE_DOMAINS


def build_host_row(
    name: str, h: dict, vm_cache: dict[str | None, dict | None], erp_user: str,
) -> dict:
    hv     = h.get("hypervisor") or None
    vm_map = vm_cache.get(hv)
    if vm_map is None:
        provisioned, vm_state = None, None
    elif name in vm_map:
        provisioned = vm_map[name]["provisioned"]
        vm_state    = vm_map[name]["vm_state"]
    else:
        provisioned, vm_state = False, None

    groups = h.get("ansible_groups", [])
    if "production" in groups:
        zone_key = "production"
    elif "staging" in groups:
        zone_key = "staging"
    else:
        zone_key = "development"

    hostname = h.get("hostname", name)
    wg_role  = h.get("wg_role", "spoke")
    domain   = ZONE_DOMAINS[zone_key]
    erp_url  = f"https://{hostname}.{domain}" if wg_role == "spoke" else ""

    return {
        "id":             name,
        "hostname":       hostname,
        "nickname":       h.get("nickname", ""),
        "virbr0_ip":      h.get("virbr0_ip", ""),
        "wg_ip":          h.get("wg_ip", ""),
        "wg_role":        wg_role,
        "backend":        h.get("backend", "kvm"),
        "hypervisor":     hv or "",
        "provisioned":    provisioned,
        "vm_state":       vm_state,
        "ansible_groups": groups,
        "vm_role":        h.get("vm_role", "dev"),
        "erp_user":       erp_user,
        "erp_url":        erp_url,
    }
