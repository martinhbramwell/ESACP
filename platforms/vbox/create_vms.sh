#!/usr/bin/env bash
# create_vms.sh — Instantiate all 3 VirtualBox VMs from esacp-base.ova.
#
# Counterpart to destroy_vms.sh. Does only VM instantiation:
#   1. Import + start all 3 VMs
#   2. Resume any savestated VMs
#   3. Detect saconsole LAN IP (Guest Additions polling)
#   4. Update ansible/inventory/dev.yml + group_vars/vbox.yml with the live IP
#   5. Clear stale known_hosts entries
#   6. Wait for SSH on all 3 VMs
#
# Writes detected console IP to /tmp/.esacp_console_ip for callers (e.g. build_lab.sh).
#
# Prerequisites:
#   - esacp-base.ova at D:\VM_images\
#   - sshpass installed (apt install sshpass)
#
# Usage (from project root):
#   bash platforms/vbox/create_vms.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

BOOTSTRAP_USER="you"
BOOTSTRAP_PASSWORD="wawa"

find_vboxmanage() {
    for candidate in "VBoxManage" "VBoxManage.exe"; do
        command -v "${candidate}" &>/dev/null && echo "${candidate}" && return
    done
    local p="/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"
    [[ -f "${p}" ]] && echo "${p}" && return
    echo ""
}

VBM="$(find_vboxmanage)"
[[ -z "${VBM}" ]] && echo "ERROR: VBoxManage not found." && exit 1

hdr() { echo ""; echo "════════════════════════════════════════"; echo "  $1"; echo "════════════════════════════════════════"; }

# ── Pre-flight: check if VMs already exist ────────────────────────────────────

EXISTING=()
for vm in console target1 target2; do
    "${VBM}" showvminfo "${vm}" --machinereadable &>/dev/null && EXISTING+=("${vm}") || true
done

if [[ ${#EXISTING[@]} -gt 0 ]]; then
    echo ""
    echo "  ⚠️   The following VMs are already registered: ${EXISTING[*]}"
    echo "  Importing OVAs would fail. Options:"
    echo "    r) Revert all 3 VMs to \"Fresh Install\" snapshot (recommended)"
    echo "    d) Exit — run destroy_vms.sh first, then re-run this script"
    echo ""
    read -rp "  Choice [r/d]: " choice
    case "${choice}" in
        r|R)
            echo ""
            exec bash platforms/vbox/revert_to_fresh.sh
            ;;
        *)
            echo "  Run: bash platforms/vbox/destroy_vms.sh"
            exit 1
            ;;
    esac
fi

# ── Phase 1: Create VMs ───────────────────────────────────────────────────────

hdr "Phase 1 — Create VMs"

# Skip per-script SSH polling — a single Phase 6 SSH wait after all VMs are
# running is faster than waiting for each one sequentially.
export SKIP_SSH_WAIT=1
bash platforms/vbox/create_console.sh
bash platforms/vbox/create_target.sh target1
bash platforms/vbox/create_target.sh target2
unset SKIP_SSH_WAIT

# ── Phase 2: Resume savestated VMs ────────────────────────────────────────────

hdr "Phase 2 — Resume savestated VMs"

for vm in console target1; do
    STATE=$("${VBM}" showvminfo "${vm}" --machinereadable 2>/dev/null \
        | grep '^VMState=' | sed 's/VMState="\(.*\)"/\1/' | tr -d '\r' || echo "unknown")
    if [[ "${STATE}" == "saved" ]]; then
        echo "  Resuming ${vm}..."
        "${VBM}" startvm "${vm}" --type headless
    else
        echo "  ${vm}: ${STATE} (no resume needed)"
    fi
done

# ── Phase 3: Detect saconsole LAN IP ─────────────────────────────────────────

hdr "Phase 3 — Detect saconsole LAN IP"

echo "Polling Guest Additions for console LAN IP..."
CONSOLE_IP=""
for i in $(seq 1 24); do
    RAW=$("${VBM}" guestproperty get console '/VirtualBox/GuestInfo/Net/0/V4/IP' 2>/dev/null || true)
    CONSOLE_IP=$(echo "${RAW}" | awk '/^Value:/ {print $2}' | tr -d '\r')
    if [[ -n "${CONSOLE_IP}" && "${CONSOLE_IP}" != "No" ]]; then
        echo "  ✅  ${CONSOLE_IP}"
        break
    fi
    echo "  ${i}0s — waiting..."
    sleep 10
done

if [[ -z "${CONSOLE_IP}" || "${CONSOLE_IP}" == "No" ]]; then
    echo "ERROR: Could not auto-detect console LAN IP. Check Guest Additions in OVA."
    exit 1
fi

# ── Phase 4: Update config files ─────────────────────────────────────────────

hdr "Phase 4 — Update config files"

sed -i "s|ansible_host: \"192\.[0-9.]*\"|ansible_host: \"${CONSOLE_IP}\"|" \
    ansible/inventory/dev.yml
echo "  ✅  dev.yml: saconsole ansible_host → ${CONSOLE_IP}"

sed -i "s|wg_hub_endpoint: \"[0-9.]*\"|wg_hub_endpoint: \"${CONSOLE_IP}\"|" \
    ansible/group_vars/vbox.yml
echo "  ✅  vbox.yml: wg_hub_endpoint → ${CONSOLE_IP}"

# ── Phase 5: Clear known_hosts ────────────────────────────────────────────────

echo ""
echo "Clearing stale known_hosts entries..."
for entry in saconsole console "${CONSOLE_IP}" 10.10.0.1 10.10.0.3 10.10.0.4; do
    ssh-keygen -R "${entry}" 2>/dev/null || true
done
ssh-keygen -R "[127.0.0.1]:2222" 2>/dev/null || true
ssh-keygen -R "[127.0.0.1]:2223" 2>/dev/null || true
echo "  ✅  Done."

# ── Phase 6: Wait for SSH on all VMs ─────────────────────────────────────────

hdr "Phase 6 — Wait for SSH"

wait_ssh() {
    local host="$1" port="$2" label="$3" elapsed=0
    echo "  ${label} (${host}:${port})..."
    while true; do
        if sshpass -p "${BOOTSTRAP_PASSWORD}" ssh -p "${port}" \
               -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
               "${BOOTSTRAP_USER}@${host}" true 2>/dev/null; then
            echo "  ✅  ${label} ready."
            return 0
        fi
        sleep 5; elapsed=$((elapsed + 5))
        [[ $((elapsed % 30)) -eq 0 ]] && echo "    ${elapsed}s..."
        [[ ${elapsed} -ge 300 ]] && echo "ERROR: ${label} SSH timeout." && exit 1
    done
}

wait_ssh "${CONSOLE_IP}" 22   "saconsole"
wait_ssh "127.0.0.1"     2222 "target1"
wait_ssh "127.0.0.1"     2223 "target2"

# ── Done ─────────────────────────────────────────────────────────────────────

echo "${CONSOLE_IP}" > /tmp/.esacp_console_ip

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  All 3 VMs running. SSH confirmed."
echo ""
echo "  saconsole LAN IP: ${CONSOLE_IP}"
echo ""
echo "  Next step — bootstrap WireGuard and deploy repo:"
echo "    bash platforms/vbox/build_lab.sh"
echo "════════════════════════════════════════════════════════════════"
