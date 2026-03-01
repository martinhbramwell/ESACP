#!/usr/bin/env bash
# create_vms.sh — macOS platform stub
# NOT FUNCTIONAL — see platforms/macos/PLATFORM.md for implementation notes.
set -euo pipefail
echo "ERROR: macOS VM creation is not yet implemented."
echo "       See platforms/macos/PLATFORM.md for the implementation roadmap."
exit 1

# TODO: implement for chosen hypervisor (Parallels / VMware Fusion / QEMU)
# Key differences from KVM path:
#   - Replace virt-install with prlctl create / vmrun / qemu-system-*
#   - cloud-init seed ISO: use mkisofs (brew install cdrtools) instead of cloud-localds
#   - Network: configure NAT or bridged via hypervisor GUI/CLI
