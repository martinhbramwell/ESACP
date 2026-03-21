#!/usr/bin/env bash
# bootstrap_saconsole.sh — Idempotent bootstrap of saconsole on a remote KVM hypervisor
#
# Phases:
#   1. Preflight checks
#   2. Build saconsole seed ISO (local, cloud-localds)
#   3. Upload seed ISO to hypervisor
#   4. Create saconsole VM on hypervisor (virt-install via SSH)
#   5. Wait for autoinstall → first boot → SSH ready
#   6. Snapshot "Fresh Install"
#   7. Ansible provision saconsole (via ProxyJump through hypervisor)
#   8. Snapshot "Stage 2.2 Baseline"
#   9. Handoff: install saconsole's SSH pubkey on hypervisor
#
# Usage (from project root):
#   bash platforms/kvm/bootstrap_saconsole.sh
#
# Prerequisites:
#   - cloud-image-utils (cloud-localds) installed on this controller
#   - SSH alias 'toshy' configured in ~/.ssh/config
#   - ~/.ssh/hasan_mighty: SSH keypair authorised on KVM VM guests
#   - SOPS age key at ~/.config/sops/age/keys.txt (for Ansible secrets)
#
# Idempotency: safe to re-run at any phase. Each step checks current state
# before acting. Delete saconsole VM + seed ISO to start from scratch.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ANSIBLE_DIR="${PROJ_ROOT}/ansible"

# ── Configuration ──────────────────────────────────────────────────────────────

HYPERVISOR_ALIAS="toshy"
HYPERVISOR_USER="hasan"
HYPERVISOR_LAN_IP="192.168.40.16"   # used in next-steps guidance only

REMOTE_IMAGES_DIR="/mnt/esacp-disk/var/lib/libvirt/images"
UBUNTU_ISO_NAME="ubuntu-24.04.4-live-server-amd64.iso"

SACONSOLE_IP="192.168.122.10"
SACONSOLE_USER="you"
SSH_KEY="${HOME}/.ssh/hasan_mighty"

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
    remote virsh --connect qemu:///system dominfo saconsole &>/dev/null
}

vm_state() {
    remote virsh --connect qemu:///system domstate saconsole 2>/dev/null \
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
        "virsh --connect qemu:///system snapshot-list saconsole --name 2>/dev/null" \
        | grep -qxF "$1"
}

# SSH options used for all direct connections FROM THIS CONTROLLER TO SACONSOLE.
# UserKnownHostsFile=/dev/null: cloud-init regenerates saconsole's SSH host keys
# on first boot AFTER autoinstall completes. The key seen in Phase 5 (ssh_ready)
# differs from the key seen in Phase 9 (handoff). StrictHostKeyChecking=no alone
# is not enough — SSH still rejects a *changed* key even with that option set.
# Using /dev/null bypasses known_hosts entirely for these bootstrap connections.
SACONSOLE_SSH_OPTS=(
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
        "${SACONSOLE_SSH_OPTS[@]}" \
        "${SACONSOLE_USER}@${SACONSOLE_IP}" \
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
        "virsh --connect qemu:///system snapshot-create-as saconsole '${name}' --atomic"
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

# ── Phase 2: Build saconsole seed ISO ─────────────────────────────────────────

step "Phase 2: Build saconsole seed ISO"

SEED_ISO="${SCRIPT_DIR}/saconsole-seed.iso"
USER_DATA="${SCRIPT_DIR}/cloud-init/saconsole/user-data"
META_DATA="${SCRIPT_DIR}/cloud-init/saconsole/meta-data"

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

REMOTE_SEED="${REMOTE_IMAGES_DIR}/saconsole-seed.iso"
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

step "Phase 4: Create saconsole VM on ${HYPERVISOR_ALIAS}"

REMOTE_ISO="${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}"

if vm_exists; then
    log "VM 'saconsole' already exists on ${HYPERVISOR_ALIAS} — skipping creation."
else
    remote "test -f '${REMOTE_ISO}'" \
        || die "Ubuntu ISO not found on ${HYPERVISOR_ALIAS}: ${REMOTE_ISO}"

    log "Running virt-install on ${HYPERVISOR_ALIAS} (autoinstall will run headlessly) ..."

    # Run via SSH heredoc to avoid shell quoting issues with multi-argument commands.
    # Variables are expanded locally before being sent to the remote shell.
    #
    # --os-variant ubuntu20.04: toshiba's osinfo-db (Ubuntu 20.04 stock) tops out at
    #   ubuntu20.04 — ubuntu22.04 and ubuntu24.04 are both absent.
    # --disk pool=esacp: stores saconsole.qcow2 in the esacp pool
    #   (/mnt/esacp-disk/var/lib/libvirt/images) — system disk is 98% full.
    # --noautoconsole: returns immediately; autoinstall runs headlessly.
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" bash <<REMOTE
virt-install \
    --connect qemu:///system \
    --name saconsole \
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

step "Phase 5: Wait for saconsole to be ready"

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
                log "VM shut off — autoinstall complete. Starting saconsole ..."
                remote virsh --connect qemu:///system start saconsole
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
                    die "Autoinstall timed out after ${AUTOINSTALL_TIMEOUT}s."$'\n'"  Debug: ssh ${HYPERVISOR_ALIAS} 'virt-viewer saconsole'"
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
    log "Polling SSH on ${SACONSOLE_IP} via ${HYPERVISOR_ALIAS} ..."
    SSH_DEADLINE=$(( SECONDS + SSH_POLL_TIMEOUT ))
    until ssh_ready; do
        if [[ ${SECONDS} -ge ${SSH_DEADLINE} ]]; then
            die "SSH not ready after ${SSH_POLL_TIMEOUT}s."$'\n'"  Try: ssh -J ${HYPERVISOR_ALIAS} -i ${SSH_KEY} ${SACONSOLE_USER}@${SACONSOLE_IP}"
        fi
        log "  Waiting for SSH ..."
        sleep 5
    done
fi

log "✅  SSH ready."

# ── Phase 6: Snapshot — Fresh Install ─────────────────────────────────────────

step "Phase 6: Snapshot '${SNAPSHOT_FRESH}'"
take_snapshot "${SNAPSHOT_FRESH}"

# ── Phase 7: Ansible provision (saconsole only) ───────────────────────────────

step "Phase 7: Ansible provision saconsole"
log "ProxyJump : ${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}"
log "Limit     : saconsole (Play 4 / controller WireGuard is a separate step)"

export ANSIBLE_CONFIG="${ANSIBLE_DIR}/ansible.cfg"
export ANSIBLE_PRIVATE_KEY_FILE="${SSH_KEY}"

# ansible_ssh_common_args adds the ProxyJump to all SSH connections from Ansible.
# It is appended to ssh_args in ansible.cfg — both apply simultaneously.
# --limit saconsole skips Play 3 (target1) and Play 4 (localhost/controller).
cd "${ANSIBLE_DIR}"
ansible-playbook \
    -i inventory/kvm.yml \
    site-kvm.yml \
    --limit saconsole \
    --extra-vars "ansible_ssh_common_args='-J ${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}'"

log "✅  Ansible provision complete."

# ── Phase 8: Snapshot — Stage 2.2 Baseline ────────────────────────────────────

step "Phase 8: Snapshot '${SNAPSHOT_BASELINE}'"
take_snapshot "${SNAPSHOT_BASELINE}"

# ── Phase 9: Handoff — saconsole SSH pubkey → hypervisor ──────────────────────

step "Phase 9: Handoff"

# Generate a keypair on saconsole if one doesn't exist yet.
log "Generating SSH keypair on saconsole (if absent) ..."
ssh \
    "${SACONSOLE_SSH_OPTS[@]}" \
    "${SACONSOLE_USER}@${SACONSOLE_IP}" \
    "test -f ~/.ssh/id_ed25519 \
        || ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519 -C 'saconsole@esacp'"

# Retrieve saconsole's public key.
SACONSOLE_PUBKEY=$(ssh \
    "${SACONSOLE_SSH_OPTS[@]}" \
    "${SACONSOLE_USER}@${SACONSOLE_IP}" \
    "cat ~/.ssh/id_ed25519.pub")

# Install pubkey on hypervisor (idempotent: grep before append).
remote bash <<REMOTE
mkdir -p ~/.ssh && chmod 700 ~/.ssh
grep -qxF '${SACONSOLE_PUBKEY}' ~/.ssh/authorized_keys 2>/dev/null \
    || echo '${SACONSOLE_PUBKEY}' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
REMOTE

log "✅  saconsole SSH pubkey installed on ${HYPERVISOR_ALIAS}."
log "    saconsole can now connect: qemu+ssh://hasan@toshiba/system"

# Seed toshiba's host key into saconsole's known_hosts.
# bootstrap_targets.sh runs FROM saconsole and SSHes to toshiba with
# BatchMode=yes — on a fresh saconsole the known_hosts is empty and
# BatchMode refuses the unknown key instead of prompting.
# Base64 transfer avoids quoting/newline issues with multi-line key content.
log "Seeding ${HYPERVISOR_ALIAS} host key into saconsole known_hosts ..."
HYPER_KEYS_B64=$(ssh-keyscan -H toshiba "${HYPERVISOR_LAN_IP}" 2>/dev/null \
    | base64 -w0 || true)
ssh \
    "${SACONSOLE_SSH_OPTS[@]}" \
    "${SACONSOLE_USER}@${SACONSOLE_IP}" \
    "mkdir -p ~/.ssh
     echo '${HYPER_KEYS_B64}' | base64 -d >> ~/.ssh/known_hosts
     chmod 600 ~/.ssh/known_hosts"
log "✅  toshiba host key seeded into saconsole known_hosts."

# ── Done ──────────────────────────────────────────────────────────────────────

step "Done"
cat <<SUMMARY

  saconsole is provisioned and running on ${HYPERVISOR_ALIAS}.

  Snapshots : '${SNAPSHOT_FRESH}', '${SNAPSHOT_BASELINE}'
  Handoff   : saconsole SSH pubkey → ${HYPERVISOR_ALIAS} authorized_keys

  ── Next steps ──────────────────────────────────────────────────────────────

  1. Port-forward WireGuard on ${HYPERVISOR_ALIAS} so this controller's spoke
     can reach saconsole hub at ${HYPERVISOR_LAN_IP}:51820:

       sudo iptables -t nat -A PREROUTING -i <LAN-iface> -p udp --dport 51820 \\
           -j DNAT --to-destination ${SACONSOLE_IP}:51820
       sudo iptables -A FORWARD -p udp -d ${SACONSOLE_IP} --dport 51820 -j ACCEPT

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
