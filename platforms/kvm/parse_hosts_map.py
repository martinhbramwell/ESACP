#!/usr/bin/env python3
"""Read hosts_map.yml and emit shell variable assignments to stdout.

Usage:
    eval "$(platforms/kvm/parse_hosts_map.py hosts_map.yml)"

Outputs variables consumed by platforms/kvm/config.sh:
    ESACP_HYPERVISOR          — hypervisor hostname (from first KVM host's field)
    ESACP_KVM_VMS             — space-separated list of all KVM VM keys
    ESACP_KVM_TARGETS         — space-separated list of KVM hosts with vm_role
    ESACP_HUB_KEY             — hosts_map key for the wg_role=hub host
    ESACP_HUB_VM_NAME         — libvirt domain name of the hub
    ESACP_HUB_HOSTNAME        — OS hostname of the hub
    ESACP_HUB_DISPLAY_NAME    — UI display label for the hub
    ESACP_HUB_VIRBR0_IP       — hub's virbr0 IP
    ESACP_HUB_WG_IP           — hub's WireGuard IP
    ESACP_VM_VIRBR0_IP_<KEY>  — per-VM virbr0 IP  (KEY uppercased)
    ESACP_VM_WG_IP_<KEY>      — per-VM WireGuard IP (KEY uppercased)
    ESACP_VM_NAME_<KEY>       — per-VM libvirt domain name (KEY uppercased)

Optional field lookup mode:
    platforms/kvm/parse_hosts_map.py hosts_map.yml --field vm_name --role hub
    → prints the single value (e.g. "saconsole")
"""

import sys
from pathlib import Path

import yaml


def _find_by_role(kvm: dict, role: str) -> tuple[str, dict]:
    """Return (key, attrs) for the first KVM host matching wg_role."""
    for key, attrs in kvm.items():
        if attrs.get("wg_role") == role:
            return key, attrs
    return "", {}


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hosts_map.yml> [--field FIELD --role ROLE]",
              file=sys.stderr)
        sys.exit(1)

    hosts_map = yaml.safe_load(Path(sys.argv[1]).read_text())
    kvm = hosts_map.get("groups", {}).get("kvm", {})

    # ── Field lookup mode ────────────────────────────────────────────────────
    if "--field" in sys.argv:
        idx = sys.argv.index("--field")
        field = sys.argv[idx + 1]
        role = "hub"
        if "--role" in sys.argv:
            role = sys.argv[sys.argv.index("--role") + 1]
        _key, attrs = _find_by_role(kvm, role)
        print(attrs.get(field, ""))
        return

    # ── Full variable export mode ────────────────────────────────────────────
    all_vms: list[str] = []
    targets: list[str] = []
    hypervisor = ""

    hub_key, hub_attrs = _find_by_role(kvm, "hub")

    for key, attrs in kvm.items():
        all_vms.append(key)
        tag = key.upper().replace("-", "_")

        virbr0 = attrs.get("virbr0_ip", "")
        wg_ip = attrs.get("wg_ip", "")
        vm_name = attrs.get("vm_name", key)

        print(f'ESACP_VM_VIRBR0_IP_{tag}="{virbr0}"')
        print(f'ESACP_VM_WG_IP_{tag}="{wg_ip}"')
        print(f'ESACP_VM_NAME_{tag}="{vm_name}"')

        if attrs.get("vm_role"):
            targets.append(key)

        if not hypervisor and attrs.get("hypervisor"):
            hypervisor = attrs["hypervisor"]

    # Hub identity variables (role-based, not name-based)
    if hub_key:
        print(f'ESACP_HUB_KEY="{hub_key}"')
        print(f'ESACP_HUB_VM_NAME="{hub_attrs.get("vm_name", hub_key)}"')
        print(f'ESACP_HUB_HOSTNAME="{hub_attrs.get("hostname", hub_key)}"')
        print(f'ESACP_HUB_DISPLAY_NAME="{hub_attrs.get("display_name", hub_key)}"')
        print(f'ESACP_HUB_VIRBR0_IP="{hub_attrs.get("virbr0_ip", "")}"')
        print(f'ESACP_HUB_WG_IP="{hub_attrs.get("wg_ip", "")}"')

    print(f'ESACP_HYPERVISOR="{hypervisor}"')
    print(f'ESACP_KVM_VMS="{" ".join(all_vms)}"')
    print(f'ESACP_KVM_TARGETS="{" ".join(targets)}"')


if __name__ == "__main__":
    main()
