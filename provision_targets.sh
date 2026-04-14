#!/usr/bin/env bash
# provision_targets.sh — Run from the hub to provision/update target VMs.
#
# Connects via WireGuard (hub at 10.10.0.1; targets at 10.10.0.3, 10.10.0.4).
# Pulls latest repo changes before running Ansible.
#
# Usage:
#   bash /opt/esacp/provision_targets.sh

set -euo pipefail
cd /opt/esacp

echo "Pulling latest ESACP repo..."
git pull

echo ""
echo "Provisioning targets..."
ANSIBLE_HOST_KEY_CHECKING=false ansible-playbook \
    -i ansible/inventory/dev.yml ansible/site-vbox.yml \
    --limit targets \
    --private-key ~/.ssh/id_ed25519

echo ""
echo "✅  Targets provisioned."
