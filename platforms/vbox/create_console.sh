#!/usr/bin/env bash
# create_console.sh — Create the saconsole VM by importing the base OVA.
#
# saconsole is the WireGuard hub and observability host. It uses bridged
# networking so it receives a real LAN IP on 192.168.40.x — required so that
# target VMs can connect to it as the WireGuard endpoint.
#
# Approach: same as create_target.sh — import target1-base.ova (a manually-
# installed, clean Ubuntu 24.04 Server image). The OVA carries NAT networking
# which this script replaces with bridged on the RZ608 adapter.
#
# Usage (from project root):
#   bash platforms/vbox/create_console.sh
#
# After the script completes, it prints the LAN IP. Update BOTH:
#   ansible/inventory/dev.yml    → saconsole ansible_host: "<LAN_IP>"
#   ansible/group_vars/vbox.yml  → wg_hub_endpoint: "<LAN_IP>"
#
# Initial Ansible provision (saconsole FIRST — it is the WireGuard hub):
#   ansible-playbook ansible/site-vbox.yml -i ansible/inventory/dev.yml \
#     --limit saconsole \
#     -e "ansible_host=<LAN_IP> ansible_password=wawa ansible_become_pass=wawa"

set -euo pipefail

# ── Constants ─────────────────────────────────────────────────────────────────

VM_NAME="console"
# Bridged adapter: RZ608 is the adapter connected to the 192.168.40.x LAN.
BRIDGED_ADAPTER="Intel(R) Wi-Fi 6E AX210 160MHz"
BASE_OVA="/mnt/d/VM_images/esacp-base.ova"
BASEFOLDER_WIN="D:\\VM_images"
BOOTSTRAP_USER="you"
BOOTSTRAP_PASSWORD="wawa"

# ── Helpers ───────────────────────────────────────────────────────────────────

find_vboxmanage() {
    for candidate in "VBoxManage" "VBoxManage.exe"; do
        if command -v "${candidate}" &>/dev/null; then
            echo "${candidate}"; return
        fi
    done
    local wsl_path="/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"
    [[ -f "${wsl_path}" ]] && echo "${wsl_path}" && return
    echo ""
}

wsl_to_win() {
    command -v wslpath &>/dev/null && wslpath -w "$1" || echo "$1"
}

# ── Locate VBoxManage ─────────────────────────────────────────────────────────

VBM="$(find_vboxmanage)"
if [[ -z "${VBM}" ]]; then
    echo "ERROR: VBoxManage not found. Install VirtualBox on the Windows host."
    exit 1
fi
echo "VBoxManage: ${VBM}"

# ── Locate base OVA ───────────────────────────────────────────────────────────

if [[ ! -f "${BASE_OVA}" ]]; then
    echo "ERROR: Base OVA not found at ${BASE_OVA}"
    echo "       Recreate it by installing Ubuntu 24.04 Server manually in VirtualBox"
    echo "       then: VBoxManage export <vmname> --output D:\\VM_images\\target1-base.ova --ovf20"
    exit 1
fi
BASE_OVA_WIN=$(wsl_to_win "${BASE_OVA}")
echo "Base OVA:   ${BASE_OVA}"

# ── Performance guard: pause other running VMs ────────────────────────────────

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
    echo "  Done."
else
    echo "  No other VMs running. Good."
fi

# ── Clean up any remnants of a previous run ───────────────────────────────────

echo ""
echo "Cleaning up any previous '${VM_NAME}' VM..."
"${VBM}" controlvm "${VM_NAME}" poweroff 2>/dev/null || true
"${VBM}" unregistervm "${VM_NAME}" --delete 2>/dev/null || true

VM_DIR_WSL="/mnt/d/VM_images/${VM_NAME}"
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
echo "Importing base OVA as '${VM_NAME}'..."
echo "  Source: ${BASE_OVA}"
echo "  Dest:   ${BASEFOLDER_WIN}\\${VM_NAME}"
echo ""

"${VBM}" import "${BASE_OVA_WIN}" \
    --vsys 0 \
    --vmname "${VM_NAME}" \
    --basefolder "${BASEFOLDER_WIN}"

echo ""
echo "  ✅  Import complete."

# ── Post-import configuration ─────────────────────────────────────────────────
# Switch from NAT (inherited from OVA) to bridged so saconsole gets a real LAN
# IP that target VMs can reach as the WireGuard endpoint.

echo ""
echo "Configuring VM settings..."

"${VBM}" modifyvm "${VM_NAME}" \
    --boot1 disk \
    --boot2 none \
    --boot3 none \
    --boot4 none \
    --audio none \
    --nic1 bridged \
    --bridgeadapter1 "${BRIDGED_ADAPTER}"

echo "  ✅  Bridged networking set on adapter: ${BRIDGED_ADAPTER}"

# ── Resize disk to 32 GB ──────────────────────────────────────────────────────
# The OVA bakes a 12 GB disk — not enough for a Docker host.
# modifymedium requires the VM to be powered off (it is at this point).
# Partition + LVM expansion is handled by the Ansible common role on first provision.

echo ""
echo "Resizing disk to 32 GB..."
DISK_WIN=$("${VBM}" showvminfo "${VM_NAME}" --machinereadable \
    | grep -E '"[A-Z]+-[0-9]+-[0-9]+"=' \
    | grep -v '"none"' \
    | head -1 \
    | cut -d'=' -f2 \
    | tr -d '"')

if [[ -z "${DISK_WIN}" ]]; then
    echo "  ⚠️  Could not auto-detect disk path — skipping resize."
    echo "  Run manually: VBoxManage modifymedium disk <path> --resize 32768"
else
    echo "  Disk: ${DISK_WIN}"
    "${VBM}" modifymedium disk "${DISK_WIN}" --resize 32768
    echo "  ✅  Disk resized to 32 GB."
fi

# ── Take Fresh Install snapshot ───────────────────────────────────────────────

echo ""
echo "Taking 'Fresh Install' snapshot..."
"${VBM}" snapshot "${VM_NAME}" take "Fresh Install" \
    --description "Imported from target1-base.ova — clean Ubuntu 24.04 Server, pre-Ansible, bridged NIC"
echo "  ✅  Snapshot taken."

# ── Start VM ──────────────────────────────────────────────────────────────────

echo ""
echo "Starting VM..."
START_ERR=$("${VBM}" startvm "${VM_NAME}" --type headless 2>&1) || {
    echo "${START_ERR}"
    if echo "${START_ERR}" | grep -q "VERR_INTNET_FLT_IF_NOT_FOUND"; then
        echo ""
        echo "  ❌  VirtualBox filter driver not bound to '${BRIDGED_ADAPTER}'."
        echo "  Fix (requires Windows UI):"
        echo "    1. Open Windows Network Connections (ncpa.cpl)"
        echo "    2. Right-click '${BRIDGED_ADAPTER}' → Properties"
        echo "    3. Tick 'VirtualBox NDIS6 Bridged Networking Driver' → OK"
        echo "    4. Re-run this script."
    fi
    exit 1
}
echo "${START_ERR}"

# ── Poll for LAN IP via VirtualBox Guest Additions ───────────────────────────
# Works only if virtualbox-guest-utils is installed in the OVA. If not, the
# script will print manual discovery instructions after the timeout.

echo ""
echo "Polling for LAN IP (via VirtualBox Guest Additions)..."
IP_TIMEOUT=90
IP_ELAPSED=0
VM_IP=""
while true; do
    RAW=$("${VBM}" guestproperty get "${VM_NAME}" '/VirtualBox/GuestInfo/Net/0/V4/IP' 2>/dev/null || true)
    VM_IP=$(echo "${RAW}" | awk '/^Value:/ {print $2}')
    if [[ -n "${VM_IP}" && "${VM_IP}" != "No" ]]; then
        echo "  ✅  LAN IP: ${VM_IP}"
        break
    fi
    sleep 5
    IP_ELAPSED=$((IP_ELAPSED + 5))
    echo "  ${IP_ELAPSED}s — waiting for IP..."
    if [[ ${IP_ELAPSED} -ge ${IP_TIMEOUT} ]]; then
        echo ""
        echo "  ⚠️  IP not auto-detected (Guest Additions may not be installed)."
        echo "  Find the IP manually:"
        echo "    1. Check your router's DHCP lease table"
        echo "    2. Or: arp -n | grep -v incomplete (look for a new 192.168.40.x entry)"
        echo "    3. Or open VirtualBox Manager → console → log in → ip addr show"
        break
    fi
done

# ── Poll SSH ──────────────────────────────────────────────────────────────────
# Skipped when SKIP_SSH_WAIT=1 (set by build_lab.sh, which does its own Phase 6
# SSH wait for all VMs after all three have been created).

if [[ -n "${VM_IP}" && -z "${SKIP_SSH_WAIT:-}" ]]; then
    echo ""
    echo "Polling SSH on ${VM_IP}:22..."
    # Remove any stale known_hosts entry for this IP
    ssh-keygen -R "${VM_IP}" 2>/dev/null || true

    SSH_TIMEOUT=300
    SSH_ELAPSED=0
    while true; do
        if sshpass -p "${BOOTSTRAP_PASSWORD}" ssh \
               -o StrictHostKeyChecking=no \
               -o ConnectTimeout=5 \
               "${BOOTSTRAP_USER}@${VM_IP}" true 2>/dev/null; then
            echo "  ✅  SSH ready."
            break
        fi
        sleep 5
        SSH_ELAPSED=$((SSH_ELAPSED + 5))
        echo "  ${SSH_ELAPSED}s — waiting for SSH..."
        if [[ ${SSH_ELAPSED} -ge ${SSH_TIMEOUT} ]]; then
            echo "  ⚠️  SSH did not respond within ${SSH_TIMEOUT}s."
            echo "  If Guest Additions are not installed, key auth may not be set up."
            echo "  Try: ssh -o StrictHostKeyChecking=no ${BOOTSTRAP_USER}@${VM_IP}"
            break
        fi
    done
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅  VM '${VM_NAME}' (saconsole) created."
echo ""
if [[ -n "${VM_IP}" ]]; then
    echo "  LAN IP detected: ${VM_IP}"
    echo ""
    echo "  ⚠️  UPDATE THESE TWO FILES before provisioning:"
    echo "     ansible/inventory/dev.yml    → saconsole ansible_host: \"${VM_IP}\""
    echo "     ansible/group_vars/vbox.yml  → wg_hub_endpoint: \"${VM_IP}\""
    echo ""
else
    echo "  LAN IP: NOT auto-detected — find manually (see instructions above)."
    echo ""
    echo "  ⚠️  After finding the IP, update BOTH:"
    echo "     ansible/inventory/dev.yml    → saconsole ansible_host: \"<LAN_IP>\""
    echo "     ansible/group_vars/vbox.yml  → wg_hub_endpoint: \"<LAN_IP>\""
    echo ""
fi
echo "  Bootstrap credentials: user=${BOOTSTRAP_USER}  password=${BOOTSTRAP_PASSWORD}"
echo ""
echo "  Bootstrap SSH:"
echo "    ssh ${BOOTSTRAP_USER}@${VM_IP:-<LAN_IP>}"
echo ""
echo "  Initial Ansible provision (saconsole FIRST — it is the WireGuard hub):"
echo "    ansible-playbook ansible/site-vbox.yml -i ansible/inventory/dev.yml \\"
echo "      --limit saconsole \\"
echo "      -e \"ansible_host=${VM_IP:-<LAN_IP>} ansible_password=wawa ansible_become_pass=wawa\""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
