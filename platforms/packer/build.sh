#!/usr/bin/env bash
# build.sh — Orchestrate the ERPNext v13 Packer image build
#
# Runs FROM the hub as user 'you'.
# Creates a short-lived build VM on toshiba, hands it to Packer (null builder),
# exports the resulting qcow2, then destroys the VM.
#
# Output: /mnt/esacp-disk/packer-output/erpnext-v13-YYYY-MM-DD.qcow2
#         (also symlinked as erpnext-v13-latest.qcow2)
#
# Usage:
#   bash platforms/packer/build.sh [--frappe-branch version-13] [--erpnext-branch version-13]
#
# Prerequisites (all met after bootstrap_hub.sh):
#   - packer installed on the hub (declared by ansible/roles/packer/; see #388)
#   - SSH access from the hub to toshiba: ssh hasan@toshiba
#   - cloud-image-utils on the hub (cloud-localds)
#   - Ubuntu 22.04 ISO on toshiba at UBUNTU_ISO_PATH

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# ── Configuration ──────────────────────────────────────────────────────────────

HYPERVISOR_ALIAS="toshiba"
HYPERVISOR_USER="hasan"

REMOTE_IMAGES_DIR="/mnt/esacp-disk/var/lib/libvirt/images"
# Metadata only — qcow2 artifact stays in the esacp libvirt pool.
# hasan can't create /mnt/esacp-disk/packer-output (owned by root);
# use home dir for the small JSON file.
METADATA_DIR="/home/${HYPERVISOR_USER}/esacp-packer-output"
UBUNTU_ISO_PATH="/var/lib/libvirt/images/ubuntu-22.04.2-live-server-amd64.iso"

BUILD_DATE="$(date +%Y-%m-%d)"
BUILD_VM="packer-build-${BUILD_DATE}"
BUILD_VM_IP="192.168.122.20"   # Reserved for packer builds — not used by any permanent VM
BUILD_VM_RAM="4096"            # ERPNext v13 requires ≥4 GB
BUILD_VM_DISK="40"             # ERPNext v13 requires ≥40 GB
BUILD_VM_VCPUS="2"

VM_USER="you"
SSH_KEY="${HOME}/.ssh/id_ed25519"

FRAPPE_BRANCH="version-13"
ERPNEXT_BRANCH="version-13"

# Read erp_user from ansible/group_vars/all.yml — single source of truth.
# Falls back to 'erpadm' if the key is absent (should not happen in normal use).
ERP_USER="$(python3 -c "
import yaml, sys
d = yaml.safe_load(open('${PROJ_ROOT}/ansible/group_vars/all.yml'))
print(d.get('erp_user', 'erpadm'))
" 2>/dev/null || echo 'erpadm')"

AUTOINSTALL_TIMEOUT=3600   # 60 min — Ubuntu autoinstall on slow hardware
SSH_POLL_TIMEOUT=120

OUTPUT_IMAGE="erpnext-v13-${BUILD_DATE}.qcow2"

# ── Parse args ─────────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --frappe-branch)  FRAPPE_BRANCH="$2";  shift 2 ;;
        --erpnext-branch) ERPNEXT_BRANCH="$2"; shift 2 ;;
        --erp-user)       ERP_USER="$2";       shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ── Helpers ────────────────────────────────────────────────────────────────────

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }
step() { echo; echo "── $* ──────────────────────────────────"; }

remote() { ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"; }

vm_exists() { remote virsh --connect qemu:///system dominfo "${BUILD_VM}" &>/dev/null; }

vm_state() {
    remote virsh --connect qemu:///system domstate "${BUILD_VM}" 2>/dev/null \
        | tr -d '\n' || echo "unknown"
}

ssh_ready() {
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes \
        -i "${SSH_KEY}" "${VM_USER}@${BUILD_VM_IP}" "echo ok" &>/dev/null
}

wait_for_vm() {
    if ssh_ready; then log "SSH already available on ${BUILD_VM}."; return; fi

    local DEADLINE=$(( SECONDS + AUTOINSTALL_TIMEOUT ))
    while :; do
        local STATE; STATE=$(vm_state)
        case "${STATE}" in
            "shut off")
                log "${BUILD_VM}: autoinstall complete — starting VM..."
                remote virsh --connect qemu:///system start "${BUILD_VM}"
                sleep 5
                break
                ;;
            running)
                ssh_ready && { log "${BUILD_VM}: SSH available."; return; }
                [[ ${SECONDS} -ge ${DEADLINE} ]] \
                    && die "Autoinstall on ${BUILD_VM} timed out after ${AUTOINSTALL_TIMEOUT}s."
                log "  ${BUILD_VM} running (autoinstall) — waiting 30s ..."
                sleep 30
                ;;
            *)
                log "  ${BUILD_VM} state: '${STATE}' — waiting 10s ..."
                sleep 10
                ;;
        esac
    done

    local SSH_DEADLINE=$(( SECONDS + SSH_POLL_TIMEOUT ))
    until ssh_ready; do
        [[ ${SECONDS} -ge ${SSH_DEADLINE} ]] \
            && die "SSH on ${BUILD_VM} not ready after ${SSH_POLL_TIMEOUT}s."
        log "  Waiting for SSH on ${BUILD_VM} ..."
        sleep 5
    done
    log "✓  ${BUILD_VM} SSH ready."
}

destroy_build_vm() {
    if vm_exists; then
        log "Destroying build VM ${BUILD_VM} ..."
        remote "virsh --connect qemu:///system destroy ${BUILD_VM} 2>/dev/null || true"
        remote "virsh --connect qemu:///system undefine ${BUILD_VM} --remove-all-storage 2>/dev/null || true"
        log "✓  ${BUILD_VM} destroyed."
    fi
    # Clear known_hosts to avoid stale key on next build
    ssh-keygen -R "${BUILD_VM_IP}" 2>/dev/null || true
}

# Always destroy the build VM on exit (success or failure)
trap 'destroy_build_vm' EXIT

# ── Phase 1: Preflight ─────────────────────────────────────────────────────────

step "Phase 1: Preflight"

command -v packer &>/dev/null || die "packer not installed on this host. \
packer is declared as a saconsole dependency by ansible/roles/packer/ (ESACP #388). \
Apply with: (cd ansible && ansible-playbook -i inventory/kvm.yml site-kvm.yml --limit saconsole --tags packer)"

command -v cloud-localds &>/dev/null \
    || die "cloud-localds not found — run: sudo apt install cloud-image-utils"

[[ -f "${SSH_KEY}" ]] || die "SSH key not found: ${SSH_KEY}"

ssh -o ConnectTimeout=5 -o BatchMode=yes \
    "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "echo ok" &>/dev/null \
    || die "Cannot reach hypervisor '${HYPERVISOR_ALIAS}'"

remote "test -f '${UBUNTU_ISO_PATH}'" \
    || die "Ubuntu ISO not found on ${HYPERVISOR_ALIAS}: ${UBUNTU_ISO_PATH}"

remote "virsh --connect qemu:///system pool-info esacp" &>/dev/null \
    || die "libvirt pool 'esacp' not active on ${HYPERVISOR_ALIAS}"

log "Preflight OK"

# ── Phase 2: Build seed ISO ────────────────────────────────────────────────────

step "Phase 2: Build seed ISO for ${BUILD_VM}"

CONTROLLER_PUBKEY="$(cat "${SSH_KEY}.pub")"
export CONTROLLER_PUBKEY

CLOUD_INIT_TEMPLATE="${SCRIPT_DIR}/cloud-init/packer-build"
SEED_ISO="${SCRIPT_DIR}/${BUILD_VM}-seed.iso"
RENDERED_USERDATA="/tmp/packer-build-userdata.yml"

[[ -d "${CLOUD_INIT_TEMPLATE}" ]] \
    || die "Cloud-init template not found: ${CLOUD_INIT_TEMPLATE}"

# Inject hub SSH pubkey
envsubst < "${CLOUD_INIT_TEMPLATE}/user-data" > "${RENDERED_USERDATA}"
cloud-localds "${SEED_ISO}" "${RENDERED_USERDATA}" "${CLOUD_INIT_TEMPLATE}/meta-data"
rm -f "${RENDERED_USERDATA}"
log "✓  Seed ISO: ${SEED_ISO}"

# ── Phase 3: Upload seed ISO ───────────────────────────────────────────────────

step "Phase 3: Upload seed ISO to ${HYPERVISOR_ALIAS}"

REMOTE_SEED="${REMOTE_IMAGES_DIR}/${BUILD_VM}-seed.iso"
scp "${SEED_ISO}" "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}:${REMOTE_SEED}"
log "✓  Seed ISO uploaded."

# ── Phase 4: Create build VM ───────────────────────────────────────────────────

step "Phase 4: Create ${BUILD_VM} on ${HYPERVISOR_ALIAS}"

# Destroy any leftover VM from a previous failed build with the same date
if vm_exists; then
    log "Leftover ${BUILD_VM} found — destroying before rebuild ..."
    destroy_build_vm
    # Disable EXIT trap temporarily to avoid double-destroy; re-enable
    trap - EXIT
    trap 'destroy_build_vm' EXIT
fi

# Clear any stale known_hosts entry before connecting
ssh-keygen -R "${BUILD_VM_IP}" 2>/dev/null || true

ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" bash <<REMOTE
virt-install \
    --connect qemu:///system \
    --name ${BUILD_VM} \
    --ram ${BUILD_VM_RAM} \
    --vcpus ${BUILD_VM_VCPUS} \
    --disk pool=esacp,size=${BUILD_VM_DISK},format=qcow2 \
    --location "${UBUNTU_ISO_PATH},kernel=casper/vmlinuz,initrd=casper/initrd" \
    --disk "path=${REMOTE_SEED},device=cdrom,readonly=on" \
    --network network=default \
    --os-variant ubuntu20.04 \
    --extra-args 'autoinstall ds=nocloud' \
    --graphics vnc \
    --noautoconsole
REMOTE
log "✓  VM '${BUILD_VM}' created."

# ── Phase 5: Wait for autoinstall + first boot ─────────────────────────────────

step "Phase 5: Wait for ${BUILD_VM} (autoinstall → first boot → SSH)"

wait_for_vm

# ── Phase 6: Packer build ──────────────────────────────────────────────────────

step "Phase 6: Packer build (null builder → SSH into ${BUILD_VM_IP})"

cd "${SCRIPT_DIR}"
packer init .
packer build \
    -var "vm_ip=${BUILD_VM_IP}" \
    -var "ssh_private_key_file=${SSH_KEY}" \
    -var "frappe_branch=${FRAPPE_BRANCH}" \
    -var "erpnext_branch=${ERPNEXT_BRANCH}" \
    -var "erp_user=${ERP_USER}" \
    erpnext-v13.pkr.hcl

log "✓  Packer build complete."

# ── Phase 7: Clone artifact to esacp pool ─────────────────────────────────────

step "Phase 7: Clone artifact to esacp pool"

# Shut down cleanly before cloning — ensures filesystem is consistent
remote "virsh --connect qemu:///system shutdown ${BUILD_VM}"
log "Waiting for ${BUILD_VM} to shut down ..."
for i in $(seq 1 30); do
    [[ "$(vm_state)" == "shut off" ]] && break
    sleep 5
done
[[ "$(vm_state)" == "shut off" ]] || die "${BUILD_VM} did not shut down cleanly."

# Remove any stale template volume with the same date
remote "virsh --connect qemu:///system vol-delete --pool esacp '${OUTPUT_IMAGE}' 2>/dev/null || true"

# Clone build VM disk to a persistent named volume in the esacp pool.
# hasan cannot write to /mnt/esacp-disk root (owned by root); virsh vol-clone
# runs through libvirtd (root) so no sudo needed.
remote "virsh --connect qemu:///system vol-clone --pool esacp '${BUILD_VM}.qcow2' '${OUTPUT_IMAGE}'"

log "✓  Template volume in esacp pool: ${OUTPUT_IMAGE}"

# ── Phase 8: Record build metadata ────────────────────────────────────────────

step "Phase 8: Record build metadata"

# Metadata goes to hasan's home dir (writable without sudo).
# api.py reads it from there via SSH to report template status.
remote "mkdir -p '${METADATA_DIR}'"
remote "cat > '${METADATA_DIR}/erpnext-v13-latest.json'" <<METADATA
{
  "image":          "${OUTPUT_IMAGE}",
  "frappe_branch":  "${FRAPPE_BRANCH}",
  "erpnext_branch": "${ERPNEXT_BRANCH}",
  "erp_user":       "${ERP_USER}",
  "built_at":       "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "built_by":       "hub:${SCRIPT_DIR}/build.sh",
  "state":          "undifferentiated"
}
METADATA

log "✓  Metadata: toshiba:${METADATA_DIR}/erpnext-v13-latest.json"

# EXIT trap destroys the build VM

step "Done — ERPNext v13 undifferentiated image ready"
echo
echo "  Volume:   esacp pool/${OUTPUT_IMAGE}  (on toshiba)"
echo "  Metadata: toshiba:${METADATA_DIR}/erpnext-v13-latest.json"
echo
echo "  Next: register as a KVM pool volume or CloudStack template,"
echo "  then 'Deploy from Template' in the Cytoscape stockroom."
echo
