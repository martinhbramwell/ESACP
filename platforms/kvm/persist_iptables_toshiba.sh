#!/usr/bin/env bash
# persist_iptables_toshiba.sh
#
# Run this DIRECTLY ON TOSHIBA (not from Mighty).
# Applies and persists the two iptables rules required for Mighty's WireGuard
# spoke to reach saconsole's hub (192.168.122.10:51820) via toshiba.
#
# Usage: bash platforms/kvm/persist_iptables_toshiba.sh
# Requires: sudo, iptables-persistent (installed automatically if absent)

set -euo pipefail

WAN_IF="wlp2s0"
SACONSOLE_IP="192.168.122.10"
WG_PORT="51820"

echo "==> Checking interface ${WAN_IF}..."
if ! ip link show "${WAN_IF}" > /dev/null 2>&1; then
  echo "ERROR: interface ${WAN_IF} not found. Check 'ip link show' and update WAN_IF."
  exit 1
fi

echo "==> Applying iptables rules..."

# DNAT: incoming WireGuard UDP on WAN → saconsole
sudo iptables -t nat -C PREROUTING \
  -i "${WAN_IF}" -p udp --dport "${WG_PORT}" \
  -j DNAT --to-destination "${SACONSOLE_IP}:${WG_PORT}" 2>/dev/null \
|| sudo iptables -t nat -A PREROUTING \
  -i "${WAN_IF}" -p udp --dport "${WG_PORT}" \
  -j DNAT --to-destination "${SACONSOLE_IP}:${WG_PORT}"

# FORWARD: allow forwarded WireGuard UDP to saconsole (must be before libvirt chains)
sudo iptables -C FORWARD \
  -i "${WAN_IF}" -o virbr0 -p udp \
  -d "${SACONSOLE_IP}" --dport "${WG_PORT}" -j ACCEPT 2>/dev/null \
|| sudo iptables -I FORWARD 1 \
  -i "${WAN_IF}" -o virbr0 -p udp \
  -d "${SACONSOLE_IP}" --dport "${WG_PORT}" -j ACCEPT

echo "==> Rules applied. Current state:"
sudo iptables -t nat -L PREROUTING -n --line-numbers | grep -E "DNAT|Chain"
sudo iptables -L FORWARD -n --line-numbers | head -8

echo "==> Installing iptables-persistent (if not present)..."
if ! dpkg -l iptables-persistent &>/dev/null; then
  # Pre-answer the installer's "save current rules?" prompts
  echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
  echo iptables-persistent iptables-persistent/autosave_v6 boolean false | sudo debconf-set-selections
  sudo apt-get install -y iptables-persistent
else
  echo "==> iptables-persistent already installed."
fi

echo "==> Saving rules to /etc/iptables/rules.v4..."
sudo netfilter-persistent save

echo ""
echo "Done. Rules will be restored automatically on reboot."
echo "Verify after next reboot: sudo iptables -t nat -L PREROUTING -n"
