#!/usr/bin/env bash
# build_lab.sh — Full VirtualBox lab bootstrap from scratch.
#
# Creates all 3 VMs, auto-detects saconsole LAN IP, provisions everything.
# After this script completes the lab is fully operational:
#   - saconsole: observability stack + control plane + Cytoscape at :8090
#   - target1, target2: node_exporter + MariaDB
#   - WireGuard mesh up on all nodes including WSL
#   - saconsole can re-provision targets independently
#
# Prerequisites:
#   - esacp-base.ova at D:\VM_images\
#   - SOPS age key at ~/.config/sops/age/keys.txt
#   - sshpass installed (apt install sshpass)
#
# Usage (from project root):
#   bash platforms/vbox/build_lab.sh

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

# ── Phase 1: Create VMs ───────────────────────────────────────────────────────

hdr "Phase 1 — Create VMs"

bash platforms/vbox/create_console.sh
bash platforms/vbox/create_target.sh target1
bash platforms/vbox/create_target.sh target2

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

# dev.yml: saconsole ansible_host (only the 192.168.x.x entry — targets use 10.10.x.x)
sed -i "s|ansible_host: \"192\.[0-9.]*\"|ansible_host: \"${CONSOLE_IP}\"|" \
    ansible/inventory/dev.yml
echo "  ✅  dev.yml: saconsole ansible_host → ${CONSOLE_IP}"

# vbox.yml: wg_hub_endpoint
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
        [[ ${elapsed} -ge 180 ]] && echo "ERROR: ${label} SSH timeout." && exit 1
    done
}

wait_ssh "${CONSOLE_IP}" 22   "saconsole"
wait_ssh "127.0.0.1"     2222 "target1"
wait_ssh "127.0.0.1"     2223 "target2"

# ── Phase 7: Provision saconsole (Plays 1–3) ──────────────────────────────────

hdr "Phase 7 — Provision saconsole"

ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
    -i ansible/inventory/dev.yml ansible/site-vbox.yml \
    --limit saconsole \
    -e "ansible_host=${CONSOLE_IP} ansible_password=${BOOTSTRAP_PASSWORD} ansible_become_pass=${BOOTSTRAP_PASSWORD}"

# ── Phase 8: Provision targets via NAT (Plays 1, 4, 5) ───────────────────────

hdr "Phase 8 — Provision targets"

for spec in "target1:2222" "target2:2223"; do
    vm="${spec%%:*}"
    port="${spec##*:}"
    echo ""
    echo "  Provisioning ${vm} via NAT port ${port}..."
    ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
        -i ansible/inventory/dev.yml ansible/site-vbox.yml \
        --limit "${vm}" \
        -e "ansible_host=127.0.0.1 ansible_port=${port} ansible_password=${BOOTSTRAP_PASSWORD} ansible_become_pass=${BOOTSTRAP_PASSWORD}"
done

# ── Phase 9: Push saconsole SSH key to targets ────────────────────────────────

hdr "Phase 9 — Push saconsole SSH key to targets"

SACONSOLE_KEY=$(ssh -o StrictHostKeyChecking=no \
    "${BOOTSTRAP_USER}@${CONSOLE_IP}" "cat ~/.ssh/id_ed25519.pub")

for spec in "target1:2222" "target2:2223"; do
    vm="${spec%%:*}"
    port="${spec##*:}"
    ssh -p "${port}" -o StrictHostKeyChecking=no "${BOOTSTRAP_USER}@127.0.0.1" \
        "grep -qF '${SACONSOLE_KEY}' ~/.ssh/authorized_keys 2>/dev/null \
         || echo '${SACONSOLE_KEY}' >> ~/.ssh/authorized_keys"
    echo "  ✅  saconsole key → ${vm}"
done

# ── Phase 10: WSL WireGuard ───────────────────────────────────────────────────

hdr "Phase 10 — WSL WireGuard"

if [[ -f /etc/wireguard/wg0.conf ]]; then
    sudo wg-quick down wg0 2>/dev/null || true
    sudo wg-quick up wg0
    echo "  ✅  wg0 up."
else
    echo "  No wg0.conf found — running Ansible to configure WSL WireGuard."
    echo "  (sudo password required)"
    ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
        -i ansible/inventory/dev.yml ansible/site-vbox.yml \
        --limit localhost -K
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  Lab build complete."
echo ""
echo "  Grafana:    http://${CONSOLE_IP}:3000"
echo "  Cytoscape:  http://${CONSOLE_IP}:8090"
echo "  Prometheus: http://${CONSOLE_IP}:9090"
echo ""
echo "  To re-provision targets from saconsole:"
echo "    ssh ${BOOTSTRAP_USER}@${CONSOLE_IP}"
echo "    bash /opt/esacp/provision_targets.sh"
echo "════════════════════════════════════════════════════════════════"
