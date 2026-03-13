#!/usr/bin/env bash
# revert_to_fresh.sh — Revert all 3 VMs to "Fresh Install" and bring them up.
#
# Does everything needed to reach the same state as create_vms.sh, but
# without importing OVAs — assumes VMs are already registered.
#
#   1. Revert all 3 VMs to "Fresh Install" snapshot
#   2. Start all 3 VMs
#   3. Detect saconsole LAN IP + update config files
#   4. Clear stale known_hosts entries
#   5. Wait for SSH on all 3 VMs
#
# After this script, run:
#   bash platforms/vbox/handoff_console.sh
#
# Usage (from project root):
#   bash platforms/vbox/revert_to_fresh.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

SNAPSHOT="Fresh Install"
ESACP_VMS=(console target1 target2)
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

# ── Phase 1: Revert snapshots ─────────────────────────────────────────────────

hdr "Phase 1 — Revert to \"${SNAPSHOT}\""

for vm in "${ESACP_VMS[@]}"; do
    echo "  ${vm}..."
    python3 orchestration/revertToBaseline.py --vm "${vm}" --snapshot "${SNAPSHOT}"
done

# ── Phase 2: Start all VMs ────────────────────────────────────────────────────

hdr "Phase 2 — Start VMs"

for vm in "${ESACP_VMS[@]}"; do
    echo "  Starting ${vm}..."
    "${VBM}" startvm "${vm}" --type headless
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
    echo "ERROR: Could not auto-detect console LAN IP."
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

# ── Phase 6: Wait for SSH ─────────────────────────────────────────────────────

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

echo "${CONSOLE_IP}" > /tmp/.esacp_console_ip

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  All 3 VMs at \"${SNAPSHOT}\". SSH confirmed."
echo ""
echo "  saconsole LAN IP: ${CONSOLE_IP}"
echo ""
echo "  Next step:"
echo "    bash platforms/vbox/handoff_console.sh"
echo "════════════════════════════════════════════════════════════════"
