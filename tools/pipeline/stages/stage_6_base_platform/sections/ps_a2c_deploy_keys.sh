#!/usr/bin/env bash
set -euo pipefail
# Section A2c: setup deploy keys + SSH config + askpass. Restore-mode only.
# Needs env: ERP_USER
echo "=== A2c: setup deploy keys for GitHub ==="
mkdir -p "/home/$ERP_USER/.ssh"
chmod 700 "/home/$ERP_USER/.ssh"
for key in you_gh_ce_sri you_gh_ce_sri_svc you_gh_route_planner you_gh.txt; do
    if [ -f "/tmp/$key" ]; then
        mv "/tmp/$key" "/home/$ERP_USER/.ssh/$key"
        chmod 600 "/home/$ERP_USER/.ssh/$key"
    fi
done
cp /tmp/rendered/ssh_config "/home/$ERP_USER/.ssh/config"
chmod 600 "/home/$ERP_USER/.ssh/config"
cp /tmp/rendered/gh_askpass.sh "/home/$ERP_USER/.ssh/gh_askpass.sh"
chmod 700 "/home/$ERP_USER/.ssh/gh_askpass.sh"
chown -R "$ERP_USER:$ERP_USER" "/home/$ERP_USER/.ssh"
echo "  [OK] deploy keys + SSH config installed"
