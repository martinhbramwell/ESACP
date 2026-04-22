# 09_handoff.sh — install hub SSH pubkey on hypervisor + hosts file + known_hosts.

step "Phase 9: Handoff"

# Generate a keypair on hub if one doesn't exist yet.
log "Generating SSH keypair on hub (if absent) ..."
ssh \
    "${HUB_SSH_OPTS[@]}" \
    "${HUB_USER}@${HUB_VIRBR0_IP}" \
    "test -f ~/.ssh/id_ed25519 \
        || ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519 -C '${HUB_KEY}@esacp'"

# Retrieve hub's public key.
HUB_PUBKEY=$(ssh \
    "${HUB_SSH_OPTS[@]}" \
    "${HUB_USER}@${HUB_VIRBR0_IP}" \
    "cat ~/.ssh/id_ed25519.pub")

# Install pubkey on hypervisor (idempotent: grep before append).
remote bash <<REMOTE
mkdir -p ~/.ssh && chmod 700 ~/.ssh
grep -qxF '${HUB_PUBKEY}' ~/.ssh/authorized_keys 2>/dev/null \
    || echo '${HUB_PUBKEY}' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
REMOTE

log "✅  Hub SSH pubkey installed on ${HYPERVISOR_ALIAS}."
log "    Hub can now connect: qemu+ssh://${HYPERVISOR_USER}@${ESACP_HYPERVISOR}/system"

# Add hypervisor to hub's /etc/hosts.
# A fresh hub uses 8.8.8.8/1.1.1.1 (from cloud-init) and cannot
# resolve the local hostname. Hub manages sibling VMs via
# qemu+ssh — without this, virsh calls fail with
# "Temporary failure in name resolution".
log "Adding ${ESACP_HYPERVISOR} → ${HYPERVISOR_LAN_IP} to hub /etc/hosts ..."
ssh \
    "${HUB_SSH_OPTS[@]}" \
    "${HUB_USER}@${HUB_VIRBR0_IP}" \
    "grep -qF '${ESACP_HYPERVISOR}' /etc/hosts 2>/dev/null \
         || echo '${HYPERVISOR_LAN_IP} ${ESACP_HYPERVISOR}' | sudo tee -a /etc/hosts > /dev/null"
log "✅  ${ESACP_HYPERVISOR} in hub /etc/hosts."

# Seed hypervisor's host key into hub's known_hosts.
# Hub manages sibling VMs via qemu+ssh to the hypervisor with
# BatchMode=yes — on a fresh hub the known_hosts is empty and
# BatchMode refuses the unknown key instead of prompting.
# Base64 transfer avoids quoting/newline issues with multi-line key content.
log "Seeding ${HYPERVISOR_ALIAS} host key into hub known_hosts ..."
HYPER_KEYS_B64=$(ssh-keyscan -H "${ESACP_HYPERVISOR}" "${HYPERVISOR_LAN_IP}" 2>/dev/null \
    | base64 -w0 || true)
ssh \
    "${HUB_SSH_OPTS[@]}" \
    "${HUB_USER}@${HUB_VIRBR0_IP}" \
    "mkdir -p ~/.ssh
     echo '${HYPER_KEYS_B64}' | base64 -d >> ~/.ssh/known_hosts
     chmod 600 ~/.ssh/known_hosts"
log "✅  toshiba host key seeded into hub known_hosts."

# Remove stale hub pubkeys from toshiba's authorized_keys.
# Each rebuild generates a new keypair and appends the new pubkey.
# Keep only the current hub's pubkey to avoid accumulation.
log "Replacing stale hub pubkeys on ${HYPERVISOR_ALIAS} ..."
remote bash <<REMOTE
mkdir -p ~/.ssh && chmod 700 ~/.ssh
# Remove all lines from previous hub builds (comment = ${HUB_KEY}@esacp
# or ${HUB_KEY}-control-plane), then append the current one.
grep -v '${HUB_KEY}' ~/.ssh/authorized_keys > /tmp/ak_clean 2>/dev/null || true
echo '${HUB_PUBKEY}' >> /tmp/ak_clean
mv /tmp/ak_clean ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
REMOTE
log "✅  toshiba authorized_keys updated (current hub pubkey only)."
