#!/usr/bin/env bash
# bootstrap_erpnext_lab.sh — Create target1 with Ubuntu 22.04 for ERPNext v13 lab install
#
# Runs FROM saconsole (not the controller).
# Tears down any existing target1, builds a fresh Ubuntu 22.04 VM with the specs
# required by ERPNext v13, and leaves it at a "Fresh Install" snapshot.
# Does NOT run Ansible — the ERPNext install is handled by prepareServer_0_lab.sh.
#
# Phases:
#   1. Preflight checks
#   2. Read saconsole SSH pubkey
#   3. Build seed ISO
#   4. Destroy existing target1 (if present)
#   5. Upload seed ISO + create VM
#   6. Wait for autoinstall → first boot → SSH ready
#   7. Snapshot "ERPNext Lab Fresh Install"
#
# Usage (from /opt/esacp on saconsole):
#   bash platforms/kvm/bootstrap_erpnext_lab.sh
#
# Prerequisites:
#   - cloud-image-utils installed on saconsole: sudo apt install cloud-image-utils
#   - SSH access from saconsole to toshiba via id_ed25519
#   - Ubuntu 22.04 ISO already on toshiba at UBUNTU_ISO_PATH below

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configuration ──────────────────────────────────────────────────────────────

HYPERVISOR_ALIAS="toshiba"
HYPERVISOR_USER="hasan"

# VM disk images go on the encrypted ESACP pool
REMOTE_IMAGES_DIR="/mnt/esacp-disk/var/lib/libvirt/images"

# Ubuntu 22.04 ISO is in the system libvirt default pool (not the encrypted disk)
UBUNTU_ISO_PATH="/var/lib/libvirt/images/ubuntu-22.04.2-live-server-amd64.iso"

VM="target1"
VM_IP="192.168.122.11"
VM_RAM="4096"    # ERPNext v13 requires ≥4 GB
VM_DISK="40"     # ERPNext v13 requires ≥40 GB
VM_VCPUS="2"

VM_USER="you"
SSH_KEY="${HOME}/.ssh/id_ed25519"

SNAPSHOT_FRESH="ERPNext Lab Fresh Install"

AUTOINSTALL_TIMEOUT=1800   # 30 minutes
SSH_POLL_TIMEOUT=120       # 2 minutes

# ── Helpers ────────────────────────────────────────────────────────────────────

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }
step() { echo; echo "── $* ──────────────────────────────────"; }

remote() {
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"
}

vm_exists() {
    remote virsh --connect qemu:///system dominfo "${VM}" &>/dev/null
}

vm_state() {
    remote virsh --connect qemu:///system domstate "${VM}" 2>/dev/null \
        | tr -d '\n' \
        || echo "unknown"
}

snapshot_exists() {
    local name="$1"
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
        "virsh --connect qemu:///system snapshot-list ${VM} --name 2>/dev/null" \
        | grep -qxF "${name}"
}

take_snapshot() {
    local name="$1"
    if snapshot_exists "${name}"; then
        log "Snapshot '${name}' already exists — skipping."
        return
    fi
    log "Creating snapshot '${name}' ..."
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
        "virsh --connect qemu:///system snapshot-create-as ${VM} '${name}' --atomic"
    log "✓  '${name}'"
}

ssh_ready() {
    ssh \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=5 \
        -o BatchMode=yes \
        -i "${SSH_KEY}" \
        "${VM_USER}@${VM_IP}" \
        "echo ok" &>/dev/null
}

wait_for_vm() {
    if ssh_ready; then
        log "SSH on ${VM} already available."
        return
    fi

    local DEADLINE=$(( SECONDS + AUTOINSTALL_TIMEOUT ))
    while :; do
        local STATE
        STATE=$(vm_state)
        case "${STATE}" in
            "shut off")
                log "${VM}: autoinstall complete. Starting ..."
                remote virsh --connect qemu:///system start "${VM}"
                sleep 5
                break
                ;;
            running)
                if ssh_ready; then
                    log "${VM}: SSH available."
                    return
                fi
                [[ ${SECONDS} -ge ${DEADLINE} ]] \
                    && die "Autoinstall on ${VM} timed out after ${AUTOINSTALL_TIMEOUT}s."
                log "  ${VM} running (autoinstall) — waiting 30s ..."
                sleep 30
                ;;
            *)
                log "  ${VM} state: '${STATE}' — waiting 10s ..."
                sleep 10
                ;;
        esac
    done

    local SSH_DEADLINE=$(( SECONDS + SSH_POLL_TIMEOUT ))
    until ssh_ready; do
        [[ ${SECONDS} -ge ${SSH_DEADLINE} ]] \
            && die "SSH on ${VM} not ready after ${SSH_POLL_TIMEOUT}s."
        log "  Waiting for SSH on ${VM} ..."
        sleep 5
    done
    log "✓  ${VM} SSH ready."
}

# ── Phase 1: Preflight ─────────────────────────────────────────────────────────

step "Phase 1: Preflight"

command -v cloud-localds &>/dev/null \
    || die "cloud-localds not found — run: sudo apt install cloud-image-utils"

[[ -f "${SSH_KEY}" ]] \
    || die "SSH key not found: ${SSH_KEY}"

ssh -o ConnectTimeout=5 -o BatchMode=yes \
    "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "echo ok" &>/dev/null \
    || die "Cannot reach hypervisor '${HYPERVISOR_ALIAS}'"

remote "test -d '${REMOTE_IMAGES_DIR}'" \
    || die "${HYPERVISOR_ALIAS}:${REMOTE_IMAGES_DIR} not found — is the LUKS disk mounted?"

remote "virsh --connect qemu:///system pool-info esacp" &>/dev/null \
    || die "libvirt pool 'esacp' not active on ${HYPERVISOR_ALIAS}"

remote "test -f '${UBUNTU_ISO_PATH}'" \
    || die "Ubuntu 22.04 ISO not found on ${HYPERVISOR_ALIAS}: ${UBUNTU_ISO_PATH}"

log "Preflight OK"

# ── Phase 2: Read saconsole SSH pubkey ─────────────────────────────────────────

step "Phase 2: Read saconsole SSH pubkey"

export CONTROLLER_PUBKEY
CONTROLLER_PUBKEY=$(cat "${SSH_KEY}.pub")
log "Pubkey: ${CONTROLLER_PUBKEY:0:40}..."

# ── Phase 3: Build seed ISO ────────────────────────────────────────────────────

step "Phase 3: Build seed ISO"

CLOUD_INIT_DIR="${SCRIPT_DIR}/cloud-init"
TEMPLATE_DIR="${CLOUD_INIT_DIR}/toshiba-${VM}"
SEED_ISO="${SCRIPT_DIR}/${VM}-erpnext-lab-seed.iso"
RENDERED_USERDATA="/tmp/${VM}-erpnext-lab-userdata.yml"

[[ -f "${TEMPLATE_DIR}/user-data" ]] \
    || die "Missing cloud-init template: ${TEMPLATE_DIR}/user-data"
[[ -f "${TEMPLATE_DIR}/meta-data" ]] \
    || die "Missing cloud-init template: ${TEMPLATE_DIR}/meta-data"

envsubst < "${TEMPLATE_DIR}/user-data" > "${RENDERED_USERDATA}"
cloud-localds "${SEED_ISO}" "${RENDERED_USERDATA}" "${TEMPLATE_DIR}/meta-data"
rm -f "${RENDERED_USERDATA}"
log "✓  ${SEED_ISO}"

# ── Phase 4: Destroy existing target1 ─────────────────────────────────────────

step "Phase 4: Destroy existing ${VM} (if present)"

if vm_exists; then
    STATE=$(vm_state)
    if [[ "${STATE}" == "running" ]]; then
        log "Stopping ${VM} ..."
        remote virsh --connect qemu:///system destroy "${VM}" || true
        sleep 3
    fi
    log "Undefining ${VM} (removing storage) ..."
    remote virsh --connect qemu:///system undefine "${VM}" --remove-all-storage
    log "✓  ${VM} removed."

    # Clear stale host keys
    ssh-keygen -R "${VM}" 2>/dev/null || true
    ssh-keygen -R "${VM_IP}" 2>/dev/null || true
else
    log "${VM} does not exist — nothing to destroy."
fi

# ── Phase 5: Upload seed ISO + create VM ──────────────────────────────────────

step "Phase 5: Upload seed ISO + create ${VM}"

REMOTE_SEED="${REMOTE_IMAGES_DIR}/${VM}-erpnext-lab-seed.iso"
log "Uploading seed ISO ..."
scp "${SEED_ISO}" "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}:${REMOTE_SEED}"
log "✓  Seed ISO uploaded."

log "Creating VM '${VM}' (${VM_RAM}MB RAM, ${VM_DISK}GB disk, ${VM_VCPUS} vCPU) ..."
# Note: --os-variant ubuntu20.04 is required on toshiba (Ubuntu 20.04 stock
# osinfo-db tops out there; ubuntu22.04/24.04 are absent). See CLAUDE.md.
ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" bash <<REMOTE
virt-install \
    --connect qemu:///system \
    --name ${VM} \
    --ram ${VM_RAM} \
    --vcpus ${VM_VCPUS} \
    --disk pool=esacp,size=${VM_DISK},format=qcow2 \
    --location "${UBUNTU_ISO_PATH},kernel=casper/vmlinuz,initrd=casper/initrd" \
    --disk "path=${REMOTE_SEED},device=cdrom,readonly=on" \
    --network network=default \
    --os-variant ubuntu20.04 \
    --extra-args 'autoinstall ds=nocloud' \
    --graphics vnc \
    --noautoconsole
REMOTE
log "✓  VM '${VM}' created — autoinstall running."

# ── Phase 6: Wait for first boot + SSH ────────────────────────────────────────

step "Phase 6: Wait for ${VM} to be ready"
wait_for_vm

# ── Phase 7: Snapshot — ERPNext Lab Fresh Install ─────────────────────────────

step "Phase 7: Snapshot '${SNAPSHOT_FRESH}'"
take_snapshot "${SNAPSHOT_FRESH}"

# ── Done ──────────────────────────────────────────────────────────────────────

step "Done"
cat <<SUMMARY

  ${VM} is up and running on ${HYPERVISOR_ALIAS} (Ubuntu 22.04, ${VM_RAM}MB RAM, ${VM_DISK}GB disk).
  Snapshot: '${SNAPSHOT_FRESH}'

  ── Next steps (run once, from saconsole) ────────────────────────────────────

  1. Copy ce_sri repo from controller to saconsole (run this on the controller):
       scp -r ~/projects/Logichem/ce_sri you@10.10.0.1:~/projects/

  2. Run the saconsole prerequisite checklist (see ce_sri/envars_lab_target1.sh header):
       mkdir -p ~/.ssh/secrets ~/projects
       touch ~/.ssh/secrets/lab_dummy.p12 ~/.ssh/secrets/ce_sri_parms.json
       echo "dns_cloudflare_api_token = lab_dummy_not_used" > ~/.ssh/secrets/certbot-cloudflare.ini
       echo "" > ~/.ssh/secrets/dhparams_4096.pem
       mkdir -p /tmp/le_mock/etc/letsencrypt
       tar czf ~/.ssh/secrets/letsencrypt.lab.target1.local.tgz -C /tmp/le_mock . && rm -rf /tmp/le_mock
       touch ~/.ssh/secrets/envars_adm_lab_target1_local.sh
       sudo mkdir -p /opt/ce_sri && sudo chown you:you /opt/ce_sri
       ln -sf ~/.ssh/secrets/envars_adm_lab_target1_local.sh /opt/ce_sri/envars.sh
       ln -sf ~/.ssh/id_ed25519     ~/.ssh/you_lab_target1_local
       ln -sf ~/.ssh/id_ed25519.pub ~/.ssh/you_lab_target1_local.pub

  3. Add to ~/.ssh/config on saconsole:
       Host t1lab.r
           User you
           HostName 192.168.122.11
           IdentityFile ~/.ssh/id_ed25519
           StrictHostKeyChecking no
       Host t1lab
           User adm
           HostName 192.168.122.11
           IdentityFile ~/.ssh/id_ed25519
           StrictHostKeyChecking no

  4. Add to /etc/hosts on saconsole:
       192.168.122.11  lab.target1.local

  5. Populate /opt/ce_sri/envars.sh with real passwords:
       cat >> /opt/ce_sri/envars.sh <<'EOF'
       export ERP_USER_PWD="<adm Linux + ERPNext Administrator password>"
       export MYPWD="<MariaDB root password>"
       EOF

  6. Run the ERPNext v13 lab install:
       cd ~/projects/ce_sri
       bash development/initialization/prepareServer_0_lab.sh

SUMMARY
