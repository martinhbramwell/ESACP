#!/usr/bin/env bash
# bootstrap_hub.sh — Idempotent bootstrap of the hub VM on a remote KVM hypervisor
#
# Phases:
#   1. Preflight checks
#   2. Build hub seed ISO (local, cloud-localds)
#   3. Upload seed ISO to hypervisor
#   4. Create hub VM on hypervisor (virt-install via SSH)
#   5. Wait for autoinstall → first boot → SSH ready
#   6. Snapshot "Fresh Install"
#   7. Ansible provision hub (via ProxyJump through hypervisor)
#   8. Snapshot "Stage 2.2 Baseline"
#   9. Handoff: install hub's SSH pubkey on hypervisor
#
# Usage (from project root):
#   bash platforms/kvm/bootstrap_hub.sh
#
# Prerequisites:
#   - cloud-image-utils (cloud-localds) installed on this controller
#   - SSH alias for hypervisor configured in ~/.ssh/config (see config.sh)
#   - SSH keypair for KVM VM guests (path from config.sh / ESACP_SSH_KEY)
#   - SOPS age key at ~/.config/sops/age/keys.txt (for Ansible secrets)
#
# Idempotency: safe to re-run at any phase. Each step checks current state
# before acting. Delete hub VM + seed ISO to start from scratch.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configuration (from hosts_map.yml + env overrides) ────────────────────────
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

UBUNTU_ISO_NAME="ubuntu-24.04.4-live-server-amd64.iso"

SNAPSHOT_FRESH="Fresh Install"
SNAPSHOT_BASELINE="Stage 2.2 Baseline"

AUTOINSTALL_TIMEOUT=1800   # 30 minutes — max wait for autoinstall to complete
SSH_POLL_TIMEOUT=120       # 2 minutes  — max wait for SSH after first boot

# ── Helpers ────────────────────────────────────────────────────────────────────

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }
step() { echo; echo "── $* ──────────────────────────────────"; }

remote() {
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"
}

vm_exists() {
    remote virsh --connect qemu:///system dominfo ${HUB_VM_NAME} &>/dev/null
}

vm_state() {
    remote virsh --connect qemu:///system domstate ${HUB_VM_NAME} 2>/dev/null \
        | tr -d '\n' \
        || echo "unknown"
}

snapshot_exists() {
    # Pass the command as a single double-quoted string to SSH — the remote
    # shell receives it verbatim and interprets the single quotes around the
    # snapshot name correctly.  The old "bash -c" wrapper was broken: SSH
    # joins all argv[] with spaces before the remote shell parses them, so
    # `ssh host bash -c "cmd"` became `bash -c cmd` (cmd = first word only).
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
        "virsh --connect qemu:///system snapshot-list ${HUB_VM_NAME} --name 2>/dev/null" \
        | grep -qxF "$1"
}

# SSH options used for all direct connections FROM THIS CONTROLLER TO SACONSOLE.
# UserKnownHostsFile=/dev/null: cloud-init regenerates the hub's SSH host keys
# on first boot AFTER autoinstall completes. The key seen in Phase 5 (ssh_ready)
# differs from the key seen in Phase 9 (handoff). StrictHostKeyChecking=no alone
# is not enough — SSH still rejects a *changed* key even with that option set.
# Using /dev/null bypasses known_hosts entirely for these bootstrap connections.
HUB_SSH_OPTS=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o LogLevel=ERROR
    -o ConnectTimeout=5
    -o BatchMode=yes
    -J "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}"
    -i "${SSH_KEY}"
)

ssh_ready() {
    ssh \
        "${HUB_SSH_OPTS[@]}" \
        "${HUB_USER}@${HUB_VIRBR0_IP}" \
        "echo ok" &>/dev/null
}

take_snapshot() {
    local name="$1"
    if snapshot_exists "${name}"; then
        log "  Snapshot '${name}' already exists — skipping."
        return
    fi
    log "  Creating snapshot '${name}' ..."
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
        "virsh --connect qemu:///system snapshot-create-as ${HUB_VM_NAME} '${name}' --atomic"
    log "  ✅  '${name}'"
}

# ── Phase 1: Preflight ─────────────────────────────────────────────────────────

step "Phase 1: Preflight"

command -v cloud-localds &>/dev/null \
    || die "cloud-localds not found — run: sudo apt install cloud-image-utils"

[[ -f "${SSH_KEY}" ]] \
    || die "SSH key not found: ${SSH_KEY}"

[[ -f "${HOME}/.config/sops/age/keys.txt" ]] \
    || die "SOPS age key not found: ~/.config/sops/age/keys.txt (required for Ansible vault)"

ssh -o ConnectTimeout=5 -o BatchMode=yes \
    "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "echo ok" &>/dev/null \
    || die "Cannot reach hypervisor '${HYPERVISOR_ALIAS}' — check ~/.ssh/config"

remote "test -d '${REMOTE_IMAGES_DIR}'" \
    || die "${HYPERVISOR_ALIAS}:${REMOTE_IMAGES_DIR} not found — is the LUKS disk mounted?"

remote "virsh --connect qemu:///system pool-info esacp" &>/dev/null \
    || die "libvirt pool 'esacp' not active on ${HYPERVISOR_ALIAS} — start it first"

log "Controller : ${HOSTNAME}"
log "Hypervisor : ${HYPERVISOR_ALIAS} (${HYPERVISOR_USER}@${HYPERVISOR_LAN_IP})"
log "Images dir : ${HYPERVISOR_ALIAS}:${REMOTE_IMAGES_DIR}"
log "✅  Preflight OK"

# ── Phase 2: Build hub seed ISO ─────────────────────────────────────────

step "Phase 2: Build hub seed ISO"

SEED_ISO="${SCRIPT_DIR}/${HUB_KEY}-seed.iso"
USER_DATA="${SCRIPT_DIR}/cloud-init/${HUB_KEY}/user-data"
META_DATA="${SCRIPT_DIR}/cloud-init/${HUB_KEY}/meta-data"

[[ -f "${USER_DATA}" ]] || die "Missing: ${USER_DATA}"
[[ -f "${META_DATA}" ]] || die "Missing: ${META_DATA}"

if [[ -f "${SEED_ISO}" \
    && "${SEED_ISO}" -nt "${USER_DATA}" \
    && "${SEED_ISO}" -nt "${META_DATA}" ]]; then
    log "Seed ISO is current — skipping rebuild."
else
    cloud-localds "${SEED_ISO}" "${USER_DATA}" "${META_DATA}"
    log "✅  ${SEED_ISO}"
fi

# ── Phase 3: Upload seed ISO to hypervisor ────────────────────────────────────

step "Phase 3: Upload seed ISO to ${HYPERVISOR_ALIAS}"

REMOTE_SEED="${REMOTE_IMAGES_DIR}/${HUB_KEY}-seed.iso"
LOCAL_MTIME=$(stat -c %Y "${SEED_ISO}")
REMOTE_MTIME=$(remote "stat -c %Y '${REMOTE_SEED}' 2>/dev/null || echo 0")

if [[ "${REMOTE_MTIME}" -ge "${LOCAL_MTIME}" ]]; then
    log "Remote seed ISO is current — skipping upload."
else
    log "Uploading to ${HYPERVISOR_ALIAS}:${REMOTE_SEED} ..."
    scp "${SEED_ISO}" "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}:${REMOTE_SEED}"
    log "✅  Uploaded."
fi

# ── Phase 4: Create VM on hypervisor ──────────────────────────────────────────

step "Phase 4: Create hub VM on ${HYPERVISOR_ALIAS}"

REMOTE_ISO="${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}"

if vm_exists; then
    log "VM '${HUB_VM_NAME}' already exists on ${HYPERVISOR_ALIAS} — skipping creation."
else
    remote "test -f '${REMOTE_ISO}'" \
        || die "Ubuntu ISO not found on ${HYPERVISOR_ALIAS}: ${REMOTE_ISO}"

    log "Running virt-install on ${HYPERVISOR_ALIAS} (autoinstall will run headlessly) ..."

    # Run via SSH heredoc to avoid shell quoting issues with multi-argument commands.
    # Variables are expanded locally before being sent to the remote shell.
    #
    # --os-variant ubuntu20.04: toshiba's osinfo-db (Ubuntu 20.04 stock) tops out at
    #   ubuntu20.04 — ubuntu22.04 and ubuntu24.04 are both absent.
    # --disk pool=esacp: stores ${HUB_VM_NAME}.qcow2 in the esacp pool
    #   (/mnt/esacp-disk/var/lib/libvirt/images) — system disk is 98% full.
    # --noautoconsole: returns immediately; autoinstall runs headlessly.
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" bash <<REMOTE
virt-install \
    --connect qemu:///system \
    --name ${HUB_VM_NAME} \
    --ram 4096 \
    --vcpus 2 \
    --disk pool=esacp,size=20,format=qcow2 \
    --location "${REMOTE_ISO},kernel=casper/vmlinuz,initrd=casper/initrd" \
    --disk "path=${REMOTE_SEED},device=cdrom,readonly=on" \
    --network network=default \
    --os-variant ubuntu20.04 \
    --extra-args 'autoinstall ds=nocloud' \
    --graphics vnc \
    --noautoconsole
REMOTE

    log "✅  VM created and autoinstall running."
fi

# ── Phase 5: Wait for first boot + SSH ────────────────────────────────────────

step "Phase 5: Wait for hub to be ready"

if ssh_ready; then
    log "SSH already available — VM is fully up."
else
    # The VM may be:
    #   a) running (autoinstall in progress — will power off when done), or
    #   b) shut off (autoinstall complete — needs to be started), or
    #   c) running (booting up after first shutdown — SSH not yet available)
    DEADLINE=$(( SECONDS + AUTOINSTALL_TIMEOUT ))
    while :; do
        STATE=$(vm_state)
        case "${STATE}" in
            "shut off")
                log "VM shut off — autoinstall complete. Starting hub ..."
                remote virsh --connect qemu:///system start ${HUB_VM_NAME}
                sleep 5
                break
                ;;
            running)
                # Could be mid-autoinstall OR post-reboot boot. Check SSH.
                if ssh_ready; then
                    log "SSH available."
                    break
                fi
                if [[ ${SECONDS} -ge ${DEADLINE} ]]; then
                    die "Autoinstall timed out after ${AUTOINSTALL_TIMEOUT}s."$'\n'"  Debug: ssh ${HYPERVISOR_ALIAS} 'virt-viewer ${HUB_VM_NAME}'"
                fi
                log "  VM running (autoinstall in progress) — waiting 30s ..."
                sleep 30
                ;;
            *)
                log "  VM state: '${STATE}' — waiting 10s ..."
                sleep 10
                ;;
        esac
    done

    # Poll until SSH responds (VM may still be booting after start).
    log "Polling SSH on ${HUB_VIRBR0_IP} via ${HYPERVISOR_ALIAS} ..."
    SSH_DEADLINE=$(( SECONDS + SSH_POLL_TIMEOUT ))
    until ssh_ready; do
        if [[ ${SECONDS} -ge ${SSH_DEADLINE} ]]; then
            die "SSH not ready after ${SSH_POLL_TIMEOUT}s."$'\n'"  Try: ssh -J ${HYPERVISOR_ALIAS} -i ${SSH_KEY} ${HUB_USER}@${HUB_VIRBR0_IP}"
        fi
        log "  Waiting for SSH ..."
        sleep 5
    done
fi

log "✅  SSH ready."

# ── Phase 6: Snapshot — Fresh Install ─────────────────────────────────────────

step "Phase 6: Snapshot '${SNAPSHOT_FRESH}'"
take_snapshot "${SNAPSHOT_FRESH}"

# ── Phase 7: Ansible provision (hub only) ───────────────────────────────

step "Phase 7: Ansible provision hub"
log "ProxyJump : ${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}"
log "Limit     : hub (Play 4 / controller WireGuard is a separate step)"

export ANSIBLE_CONFIG="${ANSIBLE_DIR}/ansible.cfg"
export ANSIBLE_PRIVATE_KEY_FILE="${SSH_KEY}"

# ansible_ssh_common_args adds the ProxyJump to all SSH connections from Ansible.
# It is appended to ssh_args in ansible.cfg — both apply simultaneously.
# --limit ${HUB_KEY} skips Play 3 (target1) and Play 4 (localhost/controller).
cd "${ANSIBLE_DIR}"
ansible-playbook \
    -i inventory/kvm.yml \
    site-kvm.yml \
    --limit ${HUB_KEY} \
    --extra-vars "ansible_ssh_common_args='-J ${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}'"

log "✅  Ansible provision complete."

# ── Phase 8: Snapshot — Stage 2.2 Baseline ────────────────────────────────────

step "Phase 8: Snapshot '${SNAPSHOT_BASELINE}'"
take_snapshot "${SNAPSHOT_BASELINE}"

# ── Phase 9: Handoff — hub SSH pubkey → hypervisor ──────────────────────

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
# resolve the local hostname. bootstrap_targets.sh uses
# HYPERVISOR_ALIAS throughout — without this, all its SSH and
# virsh calls fail with "Temporary failure in name resolution".
log "Adding ${ESACP_HYPERVISOR} → ${HYPERVISOR_LAN_IP} to hub /etc/hosts ..."
ssh \
    "${HUB_SSH_OPTS[@]}" \
    "${HUB_USER}@${HUB_VIRBR0_IP}" \
    "grep -qF '${ESACP_HYPERVISOR}' /etc/hosts 2>/dev/null \
         || echo '${HYPERVISOR_LAN_IP} ${ESACP_HYPERVISOR}' | sudo tee -a /etc/hosts > /dev/null"
log "✅  ${ESACP_HYPERVISOR} in hub /etc/hosts."

# Seed hypervisor's host key into hub's known_hosts.
# bootstrap_targets.sh runs FROM the hub and SSHes to the hypervisor with
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

# ── Done ──────────────────────────────────────────────────────────────────────

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
