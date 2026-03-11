#!/usr/bin/env bash
# create_target.sh — Create a VirtualBox target VM by importing the base OVA.
#
# Approach: import esacp-base.ova (a clean Ubuntu 24.04 Server image with
# VirtualBox Guest Additions and the operator SSH key pre-installed) rather than
# running the unattended installer. Import is seconds, not 40+ minutes.
#
# The base OVA lives at D:\VM_images\esacp-base.ova and was created by:
#   1. Manual Ubuntu Server 24.04 install via VirtualBox GUI
#   2. Install virtualbox-guest-utils inside the VM
#   3. Install operator SSH public key (~/.ssh/id_ed25519.pub) into ~/.ssh/authorized_keys
#   4. VBoxManage export <vm> --output D:\VM_images\esacp-base.ova --ovf20
#
# Network: NAT (VirtualBox built-in). WireGuard is the overlay for all
# instrumentation; physical network mode doesn't matter once WG is up.
# SSH port forwarding: target1→2222, target2→2223.
# After WireGuard is provisioned, connect via WireGuard IPs directly.
#
# Usage (from project root):
#   bash platforms/vbox/create_target.sh target1
#   bash platforms/vbox/create_target.sh target2
#
# Bootstrap SSH (before WireGuard):
#   ssh -p 2222 you@127.0.0.1
#
# Initial Ansible run:
#   ansible-playbook ansible/site-vbox.yml -i ansible/inventory/dev.yml \
#     --limit target1 -e ansible_host=127.0.0.1 -e ansible_port=2222 \
#     --ask-pass --ask-become-pass

set -euo pipefail

# ── Helpers ───────────────────────────────────────────────────────────────────

find_vboxmanage() {
    for candidate in "VBoxManage" "VBoxManage.exe"; do
        if command -v "${candidate}" &>/dev/null; then
            echo "${candidate}"; return
        fi
    done
    local wsl_path="/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"
    if [[ -f "${wsl_path}" ]]; then
        echo "${wsl_path}"; return
    fi
    echo ""
}

wsl_to_win() {
    if command -v wslpath &>/dev/null; then
        wslpath -w "$1"
    else
        echo "$1"
    fi
}

# ── Validate args ─────────────────────────────────────────────────────────────

TARGET="${1:-}"
if [[ -z "${TARGET}" ]]; then
    echo "Usage: $0 <target-name>   (e.g. target1 or target2)"
    exit 1
fi

# ── Locate VBoxManage ─────────────────────────────────────────────────────────

VBM="$(find_vboxmanage)"
if [[ -z "${VBM}" ]]; then
    echo "ERROR: VBoxManage not found. Install VirtualBox on the Windows host."
    exit 1
fi
echo "VBoxManage: ${VBM}"

# ── Locate base OVA ───────────────────────────────────────────────────────────

BASE_OVA="/mnt/d/VM_images/esacp-base.ova"
if [[ ! -f "${BASE_OVA}" ]]; then
    echo "ERROR: Base OVA not found at ${BASE_OVA}"
    echo "       Recreate it with:"
    echo "         VBoxManage export target1 --output D:\\VM_images\\target1-base.ova --ovf20"
    exit 1
fi
BASE_OVA_WIN=$(wsl_to_win "${BASE_OVA}")
echo "Base OVA:   ${BASE_OVA}"

# ── VM parameters ─────────────────────────────────────────────────────────────

# Bootstrap credentials — set during the manual install used to create the OVA.
# After WireGuard + Ansible provisioning, SSH key auth takes over.
BOOTSTRAP_USER="you"
BOOTSTRAP_PASSWORD="wawa"

case "${TARGET}" in
    target1) SSH_HOST_PORT=2222 ;;
    target2) SSH_HOST_PORT=2223 ;;
    *)       SSH_HOST_PORT=2224 ;;
esac

BASEFOLDER_WIN="D:\\VM_images"

# ── Performance guard: pause other running VMs ────────────────────────────────
# Under Hyper-V/NEM + Memory Integrity (Windows 11), running multiple VMs
# simultaneously causes severe virtual clock drift.

echo ""
echo "Checking for other running VMs..."
RUNNING_VMS=$("${VBM}" list runningvms | awk -F'"' '{print $2}')
if [[ -n "${RUNNING_VMS}" ]]; then
    echo "  Found running VMs — savestating to prevent Hyper-V timer drift:"
    while IFS= read -r vm; do
        if [[ -n "${vm}" ]]; then
            echo "    Savestating: ${vm}"
            "${VBM}" controlvm "${vm}" savestate
        fi
    done <<< "${RUNNING_VMS}"
    echo "  Done. Resume these VMs after this script completes."
else
    echo "  No other VMs running. Good."
fi

# ── Clean up any remnants of a previous run ───────────────────────────────────

echo ""
echo "Cleaning up any previous '${TARGET}' VM..."
"${VBM}" controlvm "${TARGET}" poweroff 2>/dev/null || true
"${VBM}" unregistervm "${TARGET}" --delete 2>/dev/null || true

VM_DIR_WSL="/mnt/d/VM_images/${TARGET}"
if [[ -d "${VM_DIR_WSL}" ]]; then
    echo "  Removing orphaned VM folder: ${VM_DIR_WSL}"
    rm -rf "${VM_DIR_WSL}" || {
        echo "ERROR: Cannot remove ${VM_DIR_WSL} — VBox.log may be kernel-locked."
        echo "       Reboot Windows, delete the folder, then rerun this script."
        exit 1
    }
fi

# ── Import OVA ────────────────────────────────────────────────────────────────

echo ""
echo "Importing base OVA as '${TARGET}'..."
echo "  Source: ${BASE_OVA}"
echo "  Dest:   ${BASEFOLDER_WIN}\\${TARGET}"
echo ""

"${VBM}" import "${BASE_OVA_WIN}" \
    --vsys 0 \
    --vmname "${TARGET}" \
    --basefolder "${BASEFOLDER_WIN}"

echo ""
echo "  ✅  Import complete."

# ── Post-import configuration ─────────────────────────────────────────────────
# The OVA was exported from target1 and carries its original settings.
# Fix: correct hostname, NAT port forwarding, boot order, paravirt.

echo ""
echo "Configuring VM settings..."

# Set NIC to NAT (OVA may have been exported from a bridged VM) and configure boot order.
"${VBM}" modifyvm "${TARGET}" \
    --boot1 disk \
    --boot2 none \
    --boot3 none \
    --boot4 none \
    --audio none \
    --nic1 nat

# The OVA may already have a NAT rule from the source VM. Remove it and re-add
# with the correct port for this target (2222/2223).
"${VBM}" modifyvm "${TARGET}" --natpf1 delete "ssh" 2>/dev/null || true
"${VBM}" modifyvm "${TARGET}" --natpf1 "ssh,tcp,,${SSH_HOST_PORT},,22"

# ── Verify NAT rule ───────────────────────────────────────────────────────────

echo ""
echo "Verifying NAT port forwarding rule..."
NAT_RULE=$("${VBM}" showvminfo "${TARGET}" --machinereadable 2>/dev/null \
    | grep '^Forwarding' || true)
if [[ -z "${NAT_RULE}" ]]; then
    echo "ERROR: NAT port forwarding rule was not created."
    echo "       Cannot proceed — SSH would be unreachable."
    exit 1
fi
echo "  ✅  NAT rule confirmed: ${NAT_RULE}"

# ── Take Fresh Install snapshot ───────────────────────────────────────────────

echo ""
echo "Taking 'Fresh Install' snapshot..."
"${VBM}" snapshot "${TARGET}" take "Fresh Install" \
    --description "Imported from target1-base.ova — clean Ubuntu 24.04 Server, pre-Ansible"
echo "  ✅  Snapshot taken."

# ── Start VM ──────────────────────────────────────────────────────────────────

echo ""
echo "Starting VM..."
"${VBM}" startvm "${TARGET}" --type headless

# ── Poll SSH until ready ──────────────────────────────────────────────────────

echo ""
echo "Polling SSH on 127.0.0.1:${SSH_HOST_PORT}..."
SSH_TIMEOUT=180
SSH_ELAPSED=0
while true; do
    if ssh -p "${SSH_HOST_PORT}" \
           -o StrictHostKeyChecking=no \
           -o ConnectTimeout=5 \
           -o BatchMode=yes \
           "${BOOTSTRAP_USER}@127.0.0.1" true 2>/dev/null; then
        echo "  ✅  SSH ready."
        break
    fi
    sleep 5
    SSH_ELAPSED=$((SSH_ELAPSED + 5))
    echo "  ${SSH_ELAPSED}s — waiting for SSH..."
    if [[ ${SSH_ELAPSED} -ge ${SSH_TIMEOUT} ]]; then
        echo ""
        echo "  ⚠️  SSH did not respond within ${SSH_TIMEOUT}s."
        echo "  The VM may still be booting. Retry manually:"
        echo "    ssh -p ${SSH_HOST_PORT} ${BOOTSTRAP_USER}@127.0.0.1"
        break
    fi
done

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "✅  VM '${TARGET}' is ready."
echo ""
echo "    Bootstrap credentials (password auth, first Ansible run only):"
echo "      User:     ${BOOTSTRAP_USER}"
echo "      Password: ${BOOTSTRAP_PASSWORD}"
echo "      SSH:      ssh -p ${SSH_HOST_PORT} ${BOOTSTRAP_USER}@127.0.0.1"
echo ""
echo "    Initial Ansible bootstrap (before WireGuard, using password auth):"
echo "      ansible-playbook ansible/site-vbox.yml -i ansible/inventory/dev.yml \\"
echo "        --limit ${TARGET} -e ansible_host=127.0.0.1 -e ansible_port=${SSH_HOST_PORT} \\"
echo "        --ask-pass --ask-become-pass"
echo ""
echo "    After WireGuard is provisioned, connect via WireGuard IP directly."
