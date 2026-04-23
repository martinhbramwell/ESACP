# _helpers.sh — shared helpers for bootstrap_hub phases.
# Sourced by platforms/kvm/bootstrap_hub.sh before any numbered phase.
# Assumes config.sh has already been sourced (HYPERVISOR_USER, HYPERVISOR_ALIAS,
# HUB_VM_NAME, HUB_USER, HUB_VIRBR0_IP, SSH_KEY, HUB_KEY are in scope).

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
