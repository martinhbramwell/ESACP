# 99_summary.sh — final banner with next-step operator instructions.

step "Done"
cat <<SUMMARY

  Hub is provisioned and running on ${HYPERVISOR_ALIAS}.

  Snapshots : '${SNAPSHOT_FRESH}', '${SNAPSHOT_BASELINE}'
  Handoff   : Hub SSH pubkey → ${HYPERVISOR_ALIAS} authorized_keys

  ── Next steps ──────────────────────────────────────────────────────────────

  1. Port-forward WireGuard on ${HYPERVISOR_ALIAS} so this controller's spoke
     can reach hub at ${HYPERVISOR_LAN_IP}:51820:

       sudo iptables -t nat -A PREROUTING -i <LAN-iface> -p udp --dport 51820 \\
           -j DNAT --to-destination ${HUB_VIRBR0_IP}:51820
       sudo iptables -A FORWARD -p udp -d ${HUB_VIRBR0_IP} --dport 51820 -j ACCEPT

     Verify: wg show (from this controller after step 2)

  2. Set controller WireGuard endpoint to ${HYPERVISOR_LAN_IP}:51820:
     In hosts_map.yml, update the controller spoke entry or override in a
     toshiba-specific group_vars file, then run Play 4:

       ansible-playbook -i ansible/inventory/kvm.yml ansible/site-kvm.yml \\
           --limit localhost --ask-become-pass

  3. Verify WireGuard mesh:
       python tools/esacp.py verifyVPN

  4. Validate observability stack:
       python tools/esacp.py validateObservability

SUMMARY
