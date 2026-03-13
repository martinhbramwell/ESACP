#!/usr/bin/env bash
# install_wireguard.sh — Install and configure WireGuard on all 3 VMs.
#
# Assumes all 3 VMs are running and SSH-reachable.
# Reads saconsole LAN IP from /tmp/.esacp_console_ip or ansible/inventory/dev.yml.
#
# Runs site-bootstrap.yml (WireGuard + passwordless sudo) on each VM.
# Does NOT clone the repo, deploy secrets, or bring up WSL WireGuard —
# those are handled by handoff_console.sh.
#
# Usage (from project root):
#   bash platforms/vbox/install_wireguard.sh

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

# ── Install WireGuard on all VMs ──────────────────────────────────────────────

hdr "Install WireGuard — saconsole"

ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
    -i ansible/inventory/dev.yml ansible/site-bootstrap.yml \
    --limit saconsole \
    -e "ansible_host=${CONSOLE_IP} ansible_password=${BOOTSTRAP_PASSWORD} ansible_become_pass=${BOOTSTRAP_PASSWORD}"

for spec in "target1:2222" "target2:2223"; do
    vm="${spec%%:*}"
    port="${spec##*:}"
    hdr "Install WireGuard — ${vm}"
    ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
        -i ansible/inventory/dev.yml ansible/site-bootstrap.yml \
        --limit "${vm}" \
        -e "ansible_host=127.0.0.1 ansible_port=${port} ansible_password=${BOOTSTRAP_PASSWORD} ansible_become_pass=${BOOTSTRAP_PASSWORD}"
done

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  WireGuard installed on all 3 VMs."
echo ""
echo "  Next step — clone repo + hand off to saconsole:"
echo "    bash platforms/vbox/handoff_console.sh"
echo "════════════════════════════════════════════════════════════════"
