# 01_preflight.sh — verify controller tooling + reach to hypervisor.

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
