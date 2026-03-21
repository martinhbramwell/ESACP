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

HYPERVISOR_ALIAS="toshy"
HYPERVISOR_USER="hasan"
REMOTE_IMAGES_DIR="/mnt/esacp-disk/var/lib/libvirt/images"

ESACP_VMS=(saconsole target1 target2)
declare -A VM_IPS=(
    [saconsole]="192.168.122.10"
    [target1]="192.168.122.11"
    [target2]="192.168.122.12"
)

LOCAL_SEED_ISOS=(
    saconsole-seed.iso
    target1-toshiba-seed.iso
    target2-toshiba-seed.iso
)

# ── Helpers ────────────────────────────────────────────────────────────────────

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
step() { echo; echo "── $* ──────────────────────────────────"; }

remote() {
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"
}

vm_exists() {
    remote virsh --connect qemu:///system dominfo "$1" &>/dev/null
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
    log "  ${vm}: undefining + removing storage..."
    if remote virsh --connect qemu:///system undefine "${vm}" --remove-all-storage 2>/dev/null; then
        log "  ✅  ${vm}: removed"
    else
        log "  ⚠️  ${vm}: undefine failed — storage may need manual cleanup"
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
