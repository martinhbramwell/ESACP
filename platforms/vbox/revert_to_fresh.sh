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

# shellcheck source=utils.sh
source "${SCRIPT_DIR}/utils.sh"

_tg_on_exit() {
    local rc=$?
    if [[ $rc -eq 0 ]]; then
        tg_notify "✅ revert_to_fresh — VMs at Fresh Install, SSH confirmed"
    else
        tg_notify "❌ revert_to_fresh FAILED (exit ${rc})"
    fi
}
trap '_tg_on_exit' EXIT

# ── Phase 1: Revert snapshots ─────────────────────────────────────────────────

hdr "Phase 1 — Revert to \"${SNAPSHOT}\""

for vm in "${ESACP_VMS[@]}"; do
    echo "  ${vm}..."
    python3 orchestration/revertToBaseline.py --vm "${vm}" --snapshot "${SNAPSHOT}"
done

# ── Phase 2: Start all VMs ────────────────────────────────────────────────────

hdr "Phase 2 — Start VMs"

for vm in "${ESACP_VMS[@]}"; do
    STATE=$("${VBM}" showvminfo "${vm}" --machinereadable 2>/dev/null \
        | grep '^VMState=' | cut -d'"' -f2 | tr -d '\r' || echo "unknown")
    if [[ "${STATE}" == "running" ]]; then
        echo "  ${vm}: already running — skipping."
    else
        echo "  Starting ${vm} (state: ${STATE})..."
        "${VBM}" startvm "${vm}" --type headless
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
    # Fallback: read the last-known IP from ansible/inventory/dev.yml.
    # This handles the case where the console VM is freshly imported (no Guest
    # Additions yet) but was previously reachable at its bridged DHCP address.
    FALLBACK_IP=$(grep 'ansible_host:' ansible/inventory/dev.yml \
        | head -1 | sed 's/.*"\(.*\)".*/\1/' | tr -d '[:space:]')
    if [[ -n "${FALLBACK_IP}" ]]; then
        echo "  ⚠️  Guest Additions timed out. Falling back to last-known IP from dev.yml: ${FALLBACK_IP}"
        echo "  If this IP is wrong, update ansible/inventory/dev.yml → saconsole ansible_host: \"<correct IP>\""
        CONSOLE_IP="${FALLBACK_IP}"
    else
        echo "ERROR: Could not auto-detect console LAN IP and no fallback found in dev.yml."
        exit 1
    fi
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

diag_vm() {
    local vm="$1" port="$2"
    echo "    ── diag: ${vm} ──────────────────────────────────"
    # VM state
    local state
    state=$("${VBM}" showvminfo "${vm}" --machinereadable 2>/dev/null \
        | grep '^VMState=' | cut -d'"' -f2 | tr -d '\r' || echo "unknown")
    echo "    VMState: ${state}"
    # NAT port forwarding rules (human-readable only — machinereadable omits them)
    local rules
    rules=$("${VBM}" showvminfo "${vm}" 2>/dev/null | grep -i "Rule" || true)
    if [[ -n "${rules}" ]]; then
        echo "    NAT rules:"
        echo "${rules}" | sed 's/^/      /'
    else
        echo "    NAT rules: none found"
    fi
    # TCP port reachable?
    if nc -z -w2 127.0.0.1 "${port}" 2>/dev/null; then
        echo "    TCP ${port}: open"
    else
        echo "    TCP ${port}: CLOSED (VM may still be booting)"
    fi
}

wait_ssh() {
    local host="$1" port="$2" label="$3" vm="$4" elapsed=0
    echo "  ${label} (${host}:${port})..."
    while true; do
        if sshpass -p "${BOOTSTRAP_PASSWORD}" ssh -p "${port}" \
               -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
               "${BOOTSTRAP_USER}@${host}" true 2>/dev/null; then
            echo "  ✅  ${label} ready."
            return 0
        fi
        sleep 5; elapsed=$((elapsed + 5))
        [[ $((elapsed % 60)) -eq 0 ]] && echo "    ${elapsed}s..." && diag_vm "${vm}" "${port}"
        if [[ ${elapsed} -ge 300 ]]; then
            echo ""
            echo "  ⚠️  ${label} did not become reachable after ${elapsed}s."
            echo ""
            diag_vm "${vm}" "${port}"
            "${VBM}" controlvm "${vm}" screenshotpng "/tmp/esacp_${vm}_stuck.png" 2>/dev/null || true
            echo ""
            echo "  ┌─────────────────────────────────────────────────────────────────┐"
            echo "  │  KNOWN VBOX/HYPER-V DEFECT                                      │"
            echo "  │                                                                  │"
            echo "  │  Under Memory Integrity + NEM, VMs occasionally stall during    │"
            echo "  │  kernel init and never complete the boot headlessly.             │"
            echo "  │                                                                  │"
            echo "  │  A screenshot has been saved to /tmp/esacp_${vm}_stuck.png      │"
            echo "  │                                                                  │"
            echo "  │  Run again — it almost always succeeds on the second attempt:   │"
            echo "  │    bash platforms/vbox/revert_to_fresh.sh                       │"
            echo "  └─────────────────────────────────────────────────────────────────┘"
            echo ""
            exit 1
        fi
    done
}

wait_ssh "${CONSOLE_IP}" 22   "saconsole" "console"
wait_ssh "127.0.0.1"     2222 "target1"   "target1"
wait_ssh "127.0.0.1"     2223 "target2"   "target2"

echo "${CONSOLE_IP}" > /tmp/.esacp_console_ip

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  All 3 VMs at \"${SNAPSHOT}\". SSH confirmed."
echo ""
echo "  saconsole LAN IP: ${CONSOLE_IP}"
echo ""
echo "  Next steps:"
echo "    bash platforms/vbox/install_wireguard.sh"
echo "    bash platforms/vbox/handoff_console.sh"
echo "════════════════════════════════════════════════════════════════"
