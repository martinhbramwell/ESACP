#!/usr/bin/env bash
# build_lab.sh — VirtualBox lab bootstrap (Phase 1 of 2).
#
# Phase 1 (this script — runs from WSL):
#   1. Creates all 3 VMs from esacp-base.ova
#   2. Installs WireGuard on all 3 VMs (and nothing else)
#   3. Clones ESACP repo + deploys SOPS age key to saconsole
#   4. Brings WSL WireGuard spoke up
#
# Phase 2 (runs from saconsole):
#   Run:  bash /opt/esacp/platforms/vbox/provision_targets.sh
#   Does: full Ansible provisioning (docker, observability, node_exporter, etc.)
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

# Skip per-script SSH polling — build_lab.sh does a single Phase 6 SSH wait
# for all three VMs after they are all created and resumed, which is faster
# and avoids 300s+ of wasted polling while the next VM is being imported.
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
        [[ ${elapsed} -ge 300 ]] && echo "ERROR: ${label} SSH timeout." && exit 1
    done
}

wait_ssh "${CONSOLE_IP}" 22   "saconsole"
wait_ssh "127.0.0.1"     2222 "target1"
wait_ssh "127.0.0.1"     2223 "target2"

# ── Phase 7: Bootstrap WireGuard on all VMs ──────────────────────────────────
#
# Runs site-bootstrap.yml: WireGuard + passwordless sudo only.
# Full provisioning (docker, observability, node_exporter, mariadb, etc.)
# happens from saconsole in Phase 8 / provision_targets.sh.

hdr "Phase 7 — Bootstrap WireGuard (all VMs)"

echo "  saconsole..."
ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
    -i ansible/inventory/dev.yml ansible/site-bootstrap.yml \
    --limit saconsole \
    -e "ansible_host=${CONSOLE_IP} ansible_password=${BOOTSTRAP_PASSWORD} ansible_become_pass=${BOOTSTRAP_PASSWORD}"

for spec in "target1:2222" "target2:2223"; do
    vm="${spec%%:*}"
    port="${spec##*:}"
    echo ""
    echo "  ${vm}..."
    ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
        -i ansible/inventory/dev.yml ansible/site-bootstrap.yml \
        --limit "${vm}" \
        -e "ansible_host=127.0.0.1 ansible_port=${port} ansible_password=${BOOTSTRAP_PASSWORD} ansible_become_pass=${BOOTSTRAP_PASSWORD}"
done

# ── Phase 8: Clone ESACP repo + deploy age key to saconsole ──────────────────

hdr "Phase 8 — Deploy repo + secrets to saconsole"

# The repo branch is whatever build_lab.sh is running from — keeps saconsole
# and WSL in sync during development. Change to "main" after merging.
ESACP_REPO_URL="https://github.com/martinhbramwell/ESACP.git"
ESACP_REPO_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "  Installing git on saconsole..."
sshpass -p "${BOOTSTRAP_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    "${BOOTSTRAP_USER}@${CONSOLE_IP}" \
    "sudo apt-get install -y git 2>&1 | tail -1"

echo "  Cloning ESACP (branch: ${ESACP_REPO_BRANCH}) → /opt/esacp..."
sshpass -p "${BOOTSTRAP_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    "${BOOTSTRAP_USER}@${CONSOLE_IP}" \
    "sudo mkdir -p /opt/esacp && sudo chown ${BOOTSTRAP_USER}:${BOOTSTRAP_USER} /opt/esacp && \
     git clone --branch ${ESACP_REPO_BRANCH} ${ESACP_REPO_URL} /opt/esacp"
echo "  ✅  Repo cloned."

echo "  Deploying SOPS age key..."
sshpass -p "${BOOTSTRAP_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    "${BOOTSTRAP_USER}@${CONSOLE_IP}" \
    "mkdir -p ~/.config/sops/age && chmod 700 ~/.config/sops/age"
sshpass -p "${BOOTSTRAP_PASSWORD}" scp -o StrictHostKeyChecking=no \
    ~/.config/sops/age/keys.txt \
    "${BOOTSTRAP_USER}@${CONSOLE_IP}:~/.config/sops/age/keys.txt"
sshpass -p "${BOOTSTRAP_PASSWORD}" ssh -o StrictHostKeyChecking=no \
    "${BOOTSTRAP_USER}@${CONSOLE_IP}" \
    "chmod 600 ~/.config/sops/age/keys.txt"
echo "  ✅  Age key deployed."

# ── Phase 9: WSL WireGuard ────────────────────────────────────────────────────

hdr "Phase 9 — WSL WireGuard"

# WSL WireGuard is configured directly in shell — not via Ansible.
# Ansible with become:yes + connection:local hangs inside a long-running
# pipeline because sudo -S (stdin password passing) is unreliable in that
# context. All required values are available here without Ansible.

if ! command -v wg &>/dev/null; then
    echo "  Installing wireguard-tools on WSL..."
    sudo apt-get install -y wireguard-tools
fi

echo "  Decrypting WireGuard keys..."
WG_KEYS=$(sops -d config/wireguard/keys.sops.yml)

CONTROLLER_PRIVKEY=$(python3 -c "
import sys, yaml
d = yaml.safe_load('''${WG_KEYS}''')
print(d['controller']['private_key'])
")
SACONSOLE_PUBKEY=$(python3 -c "
import sys, yaml
d = yaml.safe_load('''${WG_KEYS}''')
print(d['saconsole']['public_key'])
")
PSK=$(python3 -c "
import sys, yaml
d = yaml.safe_load('''${WG_KEYS}''')
print(d['preshared_keys']['controller_saconsole'])
")

echo "  Writing /etc/wireguard/wg0.conf..."
sudo tee /etc/wireguard/wg0.conf > /dev/null <<EOF
[Interface]
Address    = 10.10.0.2/24
PrivateKey = ${CONTROLLER_PRIVKEY}

[Peer]
PublicKey           = ${SACONSOLE_PUBKEY}
PresharedKey        = ${PSK}
AllowedIPs          = 10.10.0.0/24
Endpoint            = ${CONSOLE_IP}:51820
PersistentKeepalive = 25
EOF
sudo chmod 600 /etc/wireguard/wg0.conf

echo "  Bringing up wg0..."
sudo wg-quick down wg0 2>/dev/null || true
sudo wg-quick up wg0
echo "  ✅  wg0 up."

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  Bootstrap complete. WireGuard mesh is up."
echo ""
echo "  All 3 VMs have WireGuard configured. ESACP repo is on saconsole."
echo "  Full provisioning must now run from saconsole:"
echo ""
echo "  Option A — interactive:"
echo "    ssh ${BOOTSTRAP_USER}@${CONSOLE_IP}"
echo "    bash /opt/esacp/platforms/vbox/provision_targets.sh"
echo ""
echo "  Option B — single command from WSL:"
echo "    ssh ${BOOTSTRAP_USER}@${CONSOLE_IP} 'bash /opt/esacp/platforms/vbox/provision_targets.sh'"
echo "════════════════════════════════════════════════════════════════"
