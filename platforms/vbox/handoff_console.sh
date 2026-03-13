#!/usr/bin/env bash
# handoff_console.sh — Transfer control to saconsole.
#
# Assumes WireGuard is already installed on all 3 VMs (run install_wireguard.sh first).
# Reads saconsole LAN IP from /tmp/.esacp_console_ip or ansible/inventory/dev.yml.
#
# What this does:
#   1. Clones ESACP repo to saconsole at /opt/esacp
#   2. Deploys SOPS age key to saconsole
#   3. Brings up WSL WireGuard spoke
#
# After this script, saconsole has everything it needs to self-provision:
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
    CONSOLE_IP=$(python3 -c "
import yaml
with open('ansible/inventory/dev.yml') as f:
    inv = yaml.safe_load(f)
print(inv['all']['children']['vbox']['hosts']['saconsole']['ansible_host'])
")
fi

[[ -z "${CONSOLE_IP}" ]] && echo "ERROR: Cannot determine saconsole IP. Run create_vms.sh or revert_to_fresh.sh first." && exit 1
echo "  saconsole LAN IP: ${CONSOLE_IP}"

# ── Phase 1: Clone ESACP repo + deploy age key to saconsole ──────────────────

hdr "Phase 1 — Deploy repo + secrets to saconsole"

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

# ── Phase 2: WSL WireGuard spoke ─────────────────────────────────────────────

hdr "Phase 2 — WSL WireGuard"

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
echo "  Repo + secrets are on saconsole. Full provisioning runs from there:"
echo ""
echo "  Option A — interactive:"
echo "    ssh ${BOOTSTRAP_USER}@${CONSOLE_IP}"
echo "    bash /opt/esacp/platforms/vbox/provision_targets.sh"
echo ""
echo "  Option B — single command from WSL:"
echo "    ssh ${BOOTSTRAP_USER}@${CONSOLE_IP} 'bash /opt/esacp/platforms/vbox/provision_targets.sh'"
echo "════════════════════════════════════════════════════════════════"
