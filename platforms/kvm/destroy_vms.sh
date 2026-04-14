#!/usr/bin/env bash
# destroy_vms.sh — Cleanly destroy all ESACP VMs on the remote KVM hypervisor
#
# Safe sequence per VM:
#   1. Force-stop (virsh destroy) if running — no-op if already stopped
#   2. Undefine + remove all storage (virsh undefine --remove-all-storage)
# Also:
#   - Removes seed ISOs from local platforms/kvm/ directory (forces fresh rebuild)
#   - Removes seed ISOs from toshiba images directory
#   - Clears known_hosts entries for all VM hostnames and IPs
#
# Usage (from project root):
#   bash platforms/kvm/destroy_vms.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configuration (from hosts_map.yml + env overrides) ────────────────────────
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

# All KVM VMs and their virbr0 IPs (derived from hosts_map.yml)
# shellcheck disable=SC2206
ESACP_VMS=(${ESACP_KVM_VMS})
declare -A VM_IPS
for _vm in "${ESACP_VMS[@]}"; do
    _tag="${_vm^^}"
    _tag="${_tag//-/_}"
    eval "VM_IPS[${_vm}]=\${ESACP_VM_VIRBR0_IP_${_tag}}"
done
unset _vm _tag

# Seed ISOs: saconsole + targets (targets use <vm>-<hypervisor>-seed.iso naming)
LOCAL_SEED_ISOS=(saconsole-seed.iso)
for _vm in ${ESACP_KVM_TARGETS}; do
    LOCAL_SEED_ISOS+=("${_vm}-${ESACP_HYPERVISOR}-seed.iso")
done
unset _vm

# ── Helpers ────────────────────────────────────────────────────────────────────

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
step() { echo; echo "── $* ──────────────────────────────────"; }

remote() {
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"
}

STOP_TIMEOUT=30   # seconds to wait for a VM to reach 'shut off' after destroy

vm_exists() {
    remote virsh --connect qemu:///system dominfo "$1" &>/dev/null
}

vm_state() {
    remote virsh --connect qemu:///system domstate "$1" 2>/dev/null \
        | tr -d '[:space:]' \
        || echo "unknown"
}

# Wait for VM to reach 'shut off' after virsh destroy.
# virsh destroy sends SIGKILL but libvirt's internal state machine may take
# a moment to transition — undefine --remove-all-storage fails on a running domain.
wait_stopped() {
    local vm="$1"
    local elapsed=0
    while [[ ${elapsed} -lt ${STOP_TIMEOUT} ]]; do
        local state
        state=$(vm_state "${vm}")
        if [[ "${state}" == "shutoff" ]]; then
            return 0
        fi
        sleep 2
        elapsed=$(( elapsed + 2 ))
    done
    log "  ⚠️  ${vm}: did not reach 'shut off' within ${STOP_TIMEOUT}s (state=$(vm_state "${vm}"))"
    return 1
}

# ── Phase 1: Stop and undefine VMs ────────────────────────────────────────────

echo ""
echo "ESACP KVM — Destroy All VMs"
echo "════════════════════════════"

step "Phase 1: Stop and undefine VMs on ${HYPERVISOR_ALIAS}"

for vm in "${ESACP_VMS[@]}"; do
    if ! vm_exists "${vm}"; then
        log "  ${vm}: not registered — skipping"
        continue
    fi
    log "  ${vm}: force-stopping..."
    remote virsh --connect qemu:///system destroy "${vm}" 2>/dev/null || true
    wait_stopped "${vm}"
    log "  ${vm}: undefining + removing storage..."
    # --remove-all-storage: delete the qcow2 disk image
    # --snapshots-metadata: remove snapshot XML definitions (required when snapshots exist)
    # --managed-save: remove any managed-save state file
    if remote virsh --connect qemu:///system undefine "${vm}" \
            --remove-all-storage --snapshots-metadata --managed-save 2>&1; then
        log "  ✅  ${vm}: removed"
    else
        log "  ⚠️  ${vm}: undefine reported an error — check output above"
    fi
    echo ""
done

log "Remaining VMs on ${HYPERVISOR_ALIAS}:"
remote virsh --connect qemu:///system list --all | sed 's/^/  /'

# ── Phase 2: Remove seed ISOs ──────────────────────────────────────────────────

step "Phase 2: Remove seed ISOs (local + remote)"

for iso in "${LOCAL_SEED_ISOS[@]}"; do
    local_path="${SCRIPT_DIR}/${iso}"
    if [[ -f "${local_path}" ]]; then
        rm -f "${local_path}"
        log "  Removed local: ${iso}"
    else
        log "  Local: ${iso} — not present"
    fi
done

for iso in "${LOCAL_SEED_ISOS[@]}"; do
    remote_path="${REMOTE_IMAGES_DIR}/${iso}"
    if remote "test -f '${remote_path}'" 2>/dev/null; then
        remote "rm -f '${remote_path}'"
        log "  Removed remote: ${iso}"
    else
        log "  Remote: ${iso} — not present"
    fi
done

# ── Phase 3: Clear known_hosts ─────────────────────────────────────────────────

step "Phase 3: Clear known_hosts"

for vm in "${ESACP_VMS[@]}"; do
    ssh-keygen -R "${vm}" 2>/dev/null && log "  Cleared: ${vm}" || true
    ip="${VM_IPS[${vm}]}"
    ssh-keygen -R "${ip}" 2>/dev/null && log "  Cleared: ${ip}" || true
done

echo ""
log "✅  All ESACP VMs destroyed. Ready for fresh bootstrap."
echo ""
