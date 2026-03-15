#!/usr/bin/env bash
# provision_targets.sh — Full provisioning from saconsole.
#
# Run this from saconsole after build_lab.sh has:
#   - Installed WireGuard on all 3 VMs (mesh is up)
#   - Cloned this repo to /opt/esacp
#   - Copied the SOPS age key to ~/.config/sops/age/keys.txt
#
# This script completes everything that build_lab.sh deliberately leaves out:
#   - Installs Ansible + SOPS + Ansible collections on saconsole
#   - Runs site-vbox.yml Plays 1–5 from inside the WireGuard mesh
#     (Play 6 is tagged controller_wg and skipped — that's the WSL spoke)
#
# Usage (from saconsole, as user 'you'):
#   bash /opt/esacp/platforms/vbox/provision_targets.sh

set -euo pipefail

PROJECT_ROOT="/opt/esacp"
BECOME_PASS="wawa"
BOOTSTRAP_PASS="wawa"
SOPS_VERSION="3.9.4"

cd "${PROJECT_ROOT}"

hdr() { echo ""; echo "════════════════════════════════════════"; echo "  $1"; echo "════════════════════════════════════════"; }

# shellcheck source=utils.sh
source "${PROJECT_ROOT}/platforms/vbox/utils.sh"

_tg_on_exit() {
    local rc=$?
    if [[ $rc -eq 0 ]]; then
        tg_notify "✅ provision_targets — full Ansible provision complete"
    else
        tg_notify "❌ provision_targets FAILED (exit ${rc})"
    fi
}
trap '_tg_on_exit' EXIT

# ── Prepare saconsole SSH keypair ─────────────────────────────────────────────
#
# saconsole must be able to SSH to itself before Ansible runs.
# dev.yml has ansible_host set to the LAN IP (not localhost), so Ansible
# opens a real SSH connection even for plays targeting saconsole.
# We generate the keypair now and add it to our own authorized_keys so
# that first connection succeeds with key auth (no chicken-and-egg).
#
# The control_plane role also generates this keypair (idempotent if file exists).

hdr "Prepare SSH keypair"

if [[ ! -f ~/.ssh/id_ed25519 ]]; then
    echo "  Generating saconsole SSH keypair..."
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N '' -C saconsole-control-plane
else
    echo "  SSH keypair already exists — skipping."
fi

if ! grep -qF "$(cat ~/.ssh/id_ed25519.pub)" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "  Adding own public key to authorized_keys..."
    cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
else
    echo "  Own public key already in authorized_keys — skipping."
fi

# ── Install Ansible + SOPS ────────────────────────────────────────────────────

hdr "Install Ansible + SOPS + collections"

# Stop and mask apt-daily timers so unattended-upgrades cannot reacquire the dpkg lock.
# Stopping the service alone is not sufficient — the timers restart it.
echo "  Stopping and masking apt-daily timers..."
sudo systemctl stop unattended-upgrades apt-daily.service apt-daily-upgrade.service 2>/dev/null || true
sudo systemctl mask apt-daily.timer apt-daily-upgrade.timer apt-daily.service apt-daily-upgrade.service 2>/dev/null || true
sudo pkill -f unattended-upgrade 2>/dev/null || true

echo "  Waiting for dpkg lock to clear..."
while sudo fuser /var/lib/dpkg/lock-frontend /var/lib/apt/lists/lock \
                  /var/cache/apt/archives/lock >/dev/null 2>&1; do
    echo "    lock held — retrying in 5s..."
    sleep 5
done

sudo apt-get install -y ansible git sshpass

if ! command -v sops &>/dev/null; then
    echo "  Installing SOPS ${SOPS_VERSION}..."
    sudo curl -fsSL \
        "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64" \
        -o /usr/local/bin/sops
    sudo chmod 755 /usr/local/bin/sops
    echo "  ✅  SOPS installed."
else
    echo "  SOPS already installed — skipping."
fi

echo "  Installing Ansible collections..."
ansible-galaxy collection install -r "${PROJECT_ROOT}/ansible/requirements.yml"

# ── Full provisioning ─────────────────────────────────────────────────────────
#
# Runs site-vbox.yml Plays 1–5:
#   1. All vbox hosts: common, ssh, firewall, fail2ban, wireguard (idempotent)
#   2. saconsole: docker, observability
#   3. saconsole: control_plane (repo already cloned — update: yes is idempotent)
#   4. targets: authorise saconsole SSH key (needs saconsole_ssh_pubkey from Play 3)
#   5. targets: docker, node_exporter, mariadb
#
# Play 6 (controller_wg) is skipped — that configures the WSL spoke, not saconsole.
#
# Connection notes:
#   saconsole → itself: key auth (keypair prepared above, LAN IP in dev.yml)
#   saconsole → targets: password fallback (ansible_password=wawa) on first run;
#                         key auth after Play 4 adds saconsole's pubkey

hdr "Full provisioning (all plays)"

ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
    -i "${PROJECT_ROOT}/ansible/inventory/dev.yml" \
    "${PROJECT_ROOT}/ansible/site-vbox.yml" \
    --skip-tags controller_wg \
    -e "ansible_password=${BOOTSTRAP_PASS} ansible_become_pass=${BECOME_PASS}"

# ── Summary ───────────────────────────────────────────────────────────────────

CONSOLE_IP=$(ip -4 addr show | grep -oP '(?<=inet )192\.[0-9.]+(?=/)' | head -1 || hostname -I | awk '{print $1}')

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  Full provisioning complete."
echo ""
echo "  Grafana:    http://${CONSOLE_IP}:3000"
echo "  Prometheus: http://${CONSOLE_IP}:9090"
echo "  Cytoscape:  http://${CONSOLE_IP}:8090"
echo "════════════════════════════════════════════════════════════════"
