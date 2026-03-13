#!/usr/bin/env bash
# handoff_console.sh — Bootstrap WireGuard and transfer control to saconsole.
#
# Assumes all 3 VMs are already running and SSH-reachable (run create_vms.sh first).
# Reads the saconsole LAN IP from /tmp/.esacp_console_ip (written by create_vms.sh),
# or falls back to reading it from ansible/inventory/dev.yml.
#
# What this does:
#   1. Installs WireGuard on all 3 VMs (site-bootstrap.yml — nothing else)
#   2. Clones ESACP repo to saconsole at /opt/esacp
#   3. Deploys SOPS age key to saconsole
#   4. Brings up WSL WireGuard spoke
#
# After this script completes, WireGuard mesh is live and saconsole has
# everything it needs to self-provision. Run from saconsole:
#   bash /opt/esacp/platforms/vbox/provision_targets.sh
#
# Usage (from project root):
#   bash platforms/vbox/handoff_console.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

BOOTSTRAP_USER="you"
BOOTSTRAP_PASSWORD="wawa"

hdr() { echo ""; echo "════════════════════════════════════════"; echo "  $1"; echo "════════════════════════════════════════"; }

# ── Resolve saconsole LAN IP ──────────────────────────────────────────────────

if [[ -f /tmp/.esacp_console_ip ]]; then
    CONSOLE_IP=$(</tmp/.esacp_console_ip)
else
    # Fallback: read from dev.yml (updated by create_vms.sh Phase 4)
    CONSOLE_IP=$(python3 -c "
import yaml
with open('ansible/inventory/dev.yml') as f:
    inv = yaml.safe_load(f)
print(inv['all']['children']['vbox']['hosts']['saconsole']['ansible_host'])
")
fi

[[ -z "${CONSOLE_IP}" ]] && echo "ERROR: Cannot determine saconsole IP. Run create_vms.sh first." && exit 1
echo "  saconsole LAN IP: ${CONSOLE_IP}"

# ── Phase 1: Bootstrap WireGuard on all VMs ───────────────────────────────────

hdr "Phase 1 — Bootstrap WireGuard (all VMs)"

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

# ── Phase 2: Clone ESACP repo + deploy age key to saconsole ──────────────────

hdr "Phase 2 — Deploy repo + secrets to saconsole"

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

# ── Phase 3: WSL WireGuard ────────────────────────────────────────────────────

hdr "Phase 3 — WSL WireGuard"

if ! command -v wg &>/dev/null; then
    echo "  Installing wireguard-tools on WSL..."
    sudo apt-get install -y wireguard-tools
fi

echo "  Decrypting WireGuard keys..."
WG_KEYS=$(sops -d config/wireguard/keys.sops.yml)

CONTROLLER_PRIVKEY=$(python3 -c "
import yaml
d = yaml.safe_load('''${WG_KEYS}''')
print(d['controller']['private_key'])
")
SACONSOLE_PUBKEY=$(python3 -c "
import yaml
d = yaml.safe_load('''${WG_KEYS}''')
print(d['saconsole']['public_key'])
")
PSK=$(python3 -c "
import yaml
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
echo "  ✅  Handoff complete. WireGuard mesh is up."
echo ""
echo "  All 3 VMs have WireGuard. Repo + secrets are on saconsole."
echo "  Full provisioning runs from saconsole:"
echo ""
echo "  Option A — interactive:"
echo "    ssh ${BOOTSTRAP_USER}@${CONSOLE_IP}"
echo "    bash /opt/esacp/platforms/vbox/provision_targets.sh"
echo ""
echo "  Option B — single command from WSL:"
echo "    ssh ${BOOTSTRAP_USER}@${CONSOLE_IP} 'bash /opt/esacp/platforms/vbox/provision_targets.sh'"
echo "════════════════════════════════════════════════════════════════"
