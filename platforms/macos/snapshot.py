#!/usr/bin/env python3
"""
snapshot.py — macOS platform stub
NOT FUNCTIONAL — see platforms/macos/PLATFORM.md for implementation notes.
"""
# TODO: implement for chosen hypervisor (Parallels / VMware Fusion / QEMU)
# Mirror the interface of platforms/kvm/snapshot.py:
#   create(vm, name), revert(vm, name), list(vm), delete(vm, name), start(vm), state(vm)
#
# Parallels:  prlctl snapshot <vm> --name <name>
#             prlctl snapshot-revert <vm> --id <snapshot-id>
# VMware:     vmrun snapshot <vmx> <name>
#             vmrun revertToSnapshot <vmx> <name>

import sys
print("ERROR: macOS snapshot management is not yet implemented.", file=sys.stderr)
print("       See platforms/macos/PLATFORM.md for the implementation roadmap.", file=sys.stderr)
sys.exit(1)
