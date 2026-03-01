# Platform: macOS (Stub)

> **Status**: Not yet implemented. This directory contains non-functional stubs.
> Activate when macOS host support is required.

## Expected Implementation

| Item | KVM (implemented) | macOS (to implement) |
|---|---|---|
| Hypervisor | KVM/QEMU via libvirt | Parallels Desktop, VMware Fusion, or QEMU/HVF |
| VM lifecycle CLI | `virsh` | `prlctl` (Parallels) / `vmrun` (VMware) / `qemu-system-aarch64` |
| Snapshots | `virsh snapshot-*` | `prlctl snapshot` / `vmrun snapshot` |
| VM creation | `virt-install` | `prlctl create` / OVA import / QEMU command line |
| cloud-init | `cloud-localds` + seed ISO | Provider-dependent; QEMU supports `-drive` seed ISO |
| WireGuard install | `apt install wireguard-tools` | `brew install wireguard-tools` |
| WireGuard interface | `wg-quick@wg0` systemd unit | `wg-quick up wg0` (launchd or manual) |
| SSH key path | `${HOME}/.ssh/<keyname>` | `${HOME}/.ssh/<keyname>` |
| hosts_map platform tag | `kvm` | `macos` |

## Prerequisites (when implementing)

- Xcode Command Line Tools: `xcode-select --install`
- Homebrew: `brew install wireguard-tools`
- One of: Parallels Desktop, VMware Fusion, or QEMU (`brew install qemu`)
- `cloud-localds` equivalent: `brew install cdrtools` (provides `mkisofs`)

## Files to Implement

- `platforms/macos/create_vms.sh` — currently a stub
- `platforms/macos/snapshot.py` — currently a stub
