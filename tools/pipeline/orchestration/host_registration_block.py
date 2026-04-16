#!/usr/bin/env python3
"""YAML block builder for host registration — isolated so the primitive stays small."""

from __future__ import annotations

ZONE_GROUPS: dict[str, list[str]] = {
    "development": ["kvm", "targets", "development", "lab"],
    "staging":     ["kvm", "targets", "staging",     "lab"],
    "production":  ["kvm", "targets", "production"],
}

MARKER = "  # ── VirtualBox guests"


def build_host_block(
    *, hostname: str, nickname: str, virbr0_ip: str, wg_ip: str,
    hypervisor: str, vm_role: str, backend: str, zone: str,
) -> str:
    groups = ZONE_GROUPS.get(zone, ZONE_GROUPS["development"])
    groups_yaml = "\n".join(f"        - {g}" for g in groups)
    role_line = f"      vm_role: {vm_role}\n" if vm_role and vm_role != "dev" else ""
    return (
        f"\n    {hostname}:\n"
        f"      hostname: {hostname}\n"
        f"      nickname: {nickname or hostname[:4]}\n"
        f'      virbr0_ip: "{virbr0_ip}"\n'
        f'      wg_ip: "{wg_ip}"\n'
        f"      wg_role: spoke\n"
        f"      ansible_managed: true\n"
        f"      backend: {backend}\n"
        f"      hypervisor: {hypervisor}\n"
        f"{role_line}"
        f"      ansible_groups:\n"
        f"{groups_yaml}\n"
    )
