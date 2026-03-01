#!/usr/bin/env bash
# create_vms.sh — Create saconsole and target1 KVM VMs
#
# saconsole (Ubuntu Server 24.04.4):
#   Uses --location method with --extra-args. Fully automated, no manual step.
#
# target1 (Ubuntu Server 24.04.4):
#   Uses --location method with --extra-args. Fully automated, no manual step.
#
# Usage (from project root):
#   bash platforms/kvm/create_vms.sh [saconsole|target1|both]
#
# Default: both
#
# Prerequisites:
#   - virt-install, virsh
#   - Seed ISOs built: bash platforms/kvm/create_seeds.sh
#   - ISO symlinks present in project root

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TARGET="${1:-both}"

IMAGES_DIR="/var/lib/libvirt/images"

# Resolve symlinks so QEMU (libvirt-qemu user) can access the files without
# needing search permission on /home/hasan.
# Both VMs use the Ubuntu Server 24.04.4 ISO.
SACONSOLE_ISO="$(readlink -f "${PROJ_ROOT}/ubuntu-24.04.4-live-server-amd64.iso")"
TARGET1_ISO="$(readlink -f "${PROJ_ROOT}/ubuntu-24.04.4-live-server-amd64.iso")"

# Seed ISOs must live in IMAGES_DIR so QEMU can read them.
SACONSOLE_SEED="${IMAGES_DIR}/saconsole-seed.iso"
TARGET1_SEED="${IMAGES_DIR}/target1-seed.iso"

# ── Preflight ────────────────────────────────────────────────────────────────

for cmd in virt-install virsh; do
    if ! command -v "${cmd}" &>/dev/null; then
        echo "ERROR: '${cmd}' not found."
        exit 1
    fi
done

check_iso() {
    local path="$1" label="$2"
    if [[ ! -e "${path}" ]]; then
        echo "ERROR: ${label} not found: ${path}"
        exit 1
    fi
}

check_seed() {
    local dest="$1" vm="$2"
    local src="${SCRIPT_DIR}/${vm}-seed.iso"
    if [[ ! -f "${src}" ]]; then
        echo "ERROR: Seed ISO not found: ${src}"
        echo "       Run: bash platforms/kvm/create_seeds.sh"
        exit 1
    fi
    if [[ ! -f "${dest}" ]]; then
        echo "Copying ${vm} seed ISO to ${IMAGES_DIR}/ (needs sudo) ..."
        sudo cp "${src}" "${dest}"
    fi
}

vm_exists() {
    virsh dominfo "$1" &>/dev/null
}

# ── saconsole ────────────────────────────────────────────────────────────────

create_saconsole() {
    if vm_exists saconsole; then
        echo "VM 'saconsole' already exists — skipping. Delete it first to recreate:"
        echo "  virsh destroy saconsole; virsh undefine saconsole --remove-all-storage"
        return
    fi

    check_iso "${SACONSOLE_ISO}" "Ubuntu Server ISO"
    check_seed "${SACONSOLE_SEED}" "saconsole"

    echo "Creating saconsole VM (fully automated)..."
    # Ubuntu Server 24.04.4 live ISO; kernel/initrd under casper/.
    # The seed ISO is labeled 'cidata'; cloud-init auto-detects it (ds=nocloud).
    virt-install \
        --name saconsole \
        --ram 4096 \
        --vcpus 2 \
        --disk "path=${IMAGES_DIR}/saconsole.qcow2,size=20,format=qcow2" \
        --location "${SACONSOLE_ISO},kernel=casper/vmlinuz,initrd=casper/initrd" \
        --disk "path=${SACONSOLE_SEED},device=cdrom,readonly=on" \
        --network network=default \
        --os-variant ubuntu24.04 \
        --extra-args "autoinstall ds=nocloud" \
        --graphics vnc \
        --noautoconsole

    echo ""
    echo "✅  saconsole VM created and autoinstall running."
    echo "    Monitor: virt-viewer saconsole"
    echo "    The VM will power off when installation is complete."
}

# ── target1 ──────────────────────────────────────────────────────────────────

create_target1() {
    if vm_exists target1; then
        echo "VM 'target1' already exists — skipping. Delete it first to recreate:"
        echo "  virsh destroy target1; virsh undefine target1 --remove-all-storage"
        return
    fi

    check_iso "${TARGET1_ISO}" "Ubuntu Server ISO"
    check_seed "${TARGET1_SEED}" "target1"

    echo "Creating target1 VM (fully automated)..."
    # Ubuntu 24.04.4 live-server ISO stores kernel/initrd under casper/.
    # virt-install --location requires explicit paths for this ISO layout.
    virt-install \
        --name target1 \
        --ram 2048 \
        --vcpus 2 \
        --disk "path=${IMAGES_DIR}/target1.qcow2,size=20,format=qcow2" \
        --location "${TARGET1_ISO},kernel=casper/vmlinuz,initrd=casper/initrd" \
        --disk "path=${TARGET1_SEED},device=cdrom,readonly=on" \
        --network network=default \
        --os-variant ubuntu24.04 \
        --extra-args "autoinstall ds=nocloud" \
        --graphics vnc \
        --noautoconsole

    echo ""
    echo "✅  target1 VM created and autoinstall running."
    echo "    Monitor: virt-viewer target1"
    echo "    The VM will power off when installation is complete."
}

# ── Dispatch ─────────────────────────────────────────────────────────────────

case "${TARGET}" in
    saconsole) create_saconsole ;;
    target1)   create_target1 ;;
    both)      create_saconsole; create_target1 ;;
    *)
        echo "Usage: $0 [saconsole|target1|both]"
        exit 1
        ;;
esac
