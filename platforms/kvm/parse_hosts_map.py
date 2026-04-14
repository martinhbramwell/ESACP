#!/usr/bin/env python3
"""Read hosts_map.yml and emit shell variable assignments to stdout.

Usage:
    eval "$(platforms/kvm/parse_hosts_map.py hosts_map.yml)"

Outputs variables consumed by platforms/kvm/config.sh:
    ESACP_HYPERVISOR          — hypervisor hostname (from first KVM host's field)
    ESACP_KVM_VMS             — space-separated list of all KVM VM hostnames
    ESACP_KVM_TARGETS         — space-separated list of KVM hosts with vm_role
    ESACP_SACONSOLE_VIRBR0_IP — saconsole's virbr0 IP
    ESACP_SACONSOLE_WG_IP     — saconsole's WireGuard IP
    ESACP_VM_VIRBR0_IP_<HOST> — per-VM virbr0 IP  (HOST uppercased)
    ESACP_VM_WG_IP_<HOST>     — per-VM WireGuard IP (HOST uppercased)
"""

import sys
from pathlib import Path

import yaml


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <hosts_map.yml>", file=sys.stderr)
        sys.exit(1)

    hosts_map = yaml.safe_load(Path(sys.argv[1]).read_text())
    kvm = hosts_map.get("groups", {}).get("kvm", {})

    all_vms: list[str] = []
    targets: list[str] = []
    hypervisor = ""

    for hostname, attrs in kvm.items():
        all_vms.append(hostname)
        tag = hostname.upper().replace("-", "_")

        virbr0 = attrs.get("virbr0_ip", "")
        wg_ip = attrs.get("wg_ip", "")

        print(f'ESACP_VM_VIRBR0_IP_{tag}="{virbr0}"')
        print(f'ESACP_VM_WG_IP_{tag}="{wg_ip}"')

        if hostname == "saconsole":
            print(f'ESACP_SACONSOLE_VIRBR0_IP="{virbr0}"')
            print(f'ESACP_SACONSOLE_WG_IP="{wg_ip}"')

        if attrs.get("vm_role"):
            targets.append(hostname)

        if not hypervisor and attrs.get("hypervisor"):
            hypervisor = attrs["hypervisor"]

    print(f'ESACP_HYPERVISOR="{hypervisor}"')
    print(f'ESACP_KVM_VMS="{" ".join(all_vms)}"')
    print(f'ESACP_KVM_TARGETS="{" ".join(targets)}"')


if __name__ == "__main__":
    main()
