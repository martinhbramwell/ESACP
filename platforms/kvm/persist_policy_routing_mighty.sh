#!/bin/bash
# NetworkManager dispatcher: source-based policy routing for dual-NIC
# Ensures return traffic exits via the correct interface.
# See: https://github.com/martinhbramwell/ESACP/issues/112
#
# Install: sudo cp this file /etc/NetworkManager/dispatcher.d/10-policy-routing.sh
#          sudo chmod 755 /etc/NetworkManager/dispatcher.d/10-policy-routing.sh
#
# NM provides: $1=interface, $2=action, $IP4_ADDRESS_0="addr/prefix gateway"

IFACE="$1"
ACTION="$2"

case "$ACTION" in
    up|dhcp4-change) ;;
    *) exit 0 ;;
esac

GATEWAY="192.168.1.254"
SUBNET="192.168.1.0/24"

case "$IFACE" in
    wlp89s0)
        TABLE="wifi"
        # Extract IP from NM env (format: "192.168.1.81/24 192.168.1.254")
        SRC="${IP4_ADDRESS_0%% *}"   # "192.168.1.81/24"
        SRC="${SRC%%/*}"             # "192.168.1.81"
        ;;
    enp88s0)
        TABLE="eth0rt"
        SRC="${IP4_ADDRESS_0%% *}"
        SRC="${SRC%%/*}"
        ;;
    *) exit 0 ;;
esac

if [ -z "$SRC" ]; then
    # NM fires up twice — first without IP env; silently skip
    exit 0
fi

# Repopulate the routing table (flush first to handle IP changes)
ip route flush table "$TABLE" 2>/dev/null
ip route add "$SUBNET" dev "$IFACE" src "$SRC" table "$TABLE"
ip route add default via "$GATEWAY" dev "$IFACE" table "$TABLE"

# Add the rule if not already present
if ! ip rule show | grep -q "from $SRC lookup $TABLE"; then
    ip rule add from "$SRC" table "$TABLE"
fi

logger -t policy-routing "$IFACE ($SRC) → table $TABLE populated"
