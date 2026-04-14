#!/usr/bin/env bash
# bootstrap_targets.sh — Bootstrap target1 and target2 on the remote KVM hypervisor
#
# Runs FROM saconsole after the control_plane role has been applied.
# saconsole reaches targets directly on toshiba's virbr0 (192.168.122.0/24) —
# no ProxyJump required (saconsole and its sibling targets share the same virbr0).
#
# Phases:
#   1. Preflight checks
#   2. Read saconsole SSH pubkey
#   3. Build seed ISOs (target1, target2) with saconsole's pubkey injected
#   4. Upload seed ISOs to hypervisor
#   5. Create VMs on hypervisor
#   6. Wait for autoinstall → first boot → SSH ready (both VMs)
#   7. Snapshot "Fresh Install" (both VMs)
#   8. Ansible provision targets (from saconsole — direct virbr0 connection)
#   9. Snapshot "Stage 2.2 Targets Baseline" (both VMs)
#
# Usage (from /opt/esacp on saconsole):
#   bash platforms/kvm/bootstrap_targets.sh
#
# Prerequisites:
#   - control_plane role applied to saconsole (provides: Ansible, repo, SSH keypair)
#   - cloud-image-utils installed: sudo apt install cloud-image-utils
#   - SSH access from saconsole to hypervisor (via saconsole's ~/.ssh/id_ed25519)
#   - SOPS age key at ~/.config/sops/age/keys.txt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configuration (from hosts_map.yml + env overrides) ────────────────────────
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

# Saconsole-specific overrides: SSH key is saconsole's own keypair, not controller's
SSH_KEY="${HOME}/.ssh/id_ed25519"

UBUNTU_ISO_NAME="ubuntu-22.04.2-live-server-amd64.iso"

SNAPSHOT_FRESH="Fresh Install"
SNAPSHOT_BASELINE="Stage 2.2 Targets Baseline"

AUTOINSTALL_TIMEOUT=1800   # 30 minutes — max wait for autoinstall to complete
SSH_POLL_TIMEOUT=120       # 2 minutes  — max wait for SSH after first boot

# Targets derived from hosts_map.yml (all KVM hosts with vm_role set)
# shellcheck disable=SC2206
TARGETS=(${ESACP_KVM_TARGETS})
declare -A TARGET_IP
declare -A TARGET_RAM
for _t in "${TARGETS[@]}"; do
    _tag="${_t^^}"
    _tag="${_tag//-/_}"
    eval "TARGET_IP[${_t}]=\${ESACP_VM_VIRBR0_IP_${_tag}}"
    TARGET_RAM[${_t}]="2048"
done
unset _t _tag

# ── Helpers ────────────────────────────────────────────────────────────────────

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
die()  { echo; echo "ERROR: $*" >&2; exit 1; }
step() { echo; echo "── $* ──────────────────────────────────"; }

remote() {
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"
}

vm_exists() {
    local vm="$1"
    remote virsh --connect qemu:///system dominfo "${vm}" &>/dev/null
}

vm_state() {
    local vm="$1"
    remote virsh --connect qemu:///system domstate "${vm}" 2>/dev/null \
        | tr -d '\n' \
        || echo "unknown"
}

snapshot_exists() {
    local vm="$1" name="$2"
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
        "virsh --connect qemu:///system snapshot-list ${vm} --name 2>/dev/null" \
        | grep -qxF "${name}"
}

take_snapshot() {
    local vm="$1" name="$2"
    if snapshot_exists "${vm}" "${name}"; then
        log "  Snapshot '${name}' on ${vm} already exists — skipping."
        return
    fi
    log "  Creating snapshot '${name}' on ${vm} ..."
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
        "virsh --connect qemu:///system snapshot-create-as ${vm} '${name}' --atomic"
    log "  ✓  '${name}'"
}

ssh_ready() {
    local vm="$1" ip="$2"
    ssh \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=5 \
        -o BatchMode=yes \
        -i "${SSH_KEY}" \
        "${VM_USER}@${ip}" \
        "echo ok" &>/dev/null
}

wait_for_vm() {
    local vm="$1" ip="$2"
    if ssh_ready "${vm}" "${ip}"; then
        log "SSH on ${vm} already available."
        return
    fi

    local DEADLINE=$(( SECONDS + AUTOINSTALL_TIMEOUT ))
    while :; do
        local STATE
        STATE=$(vm_state "${vm}")
        case "${STATE}" in
            "shut off")
                log "${vm}: autoinstall complete. Starting ..."
                remote virsh --connect qemu:///system start "${vm}"
                sleep 5
                break
                ;;
            running)
                if ssh_ready "${vm}" "${ip}"; then
                    log "${vm}: SSH available."
                    return
                fi
                [[ ${SECONDS} -ge ${DEADLINE} ]] \
                    && die "Autoinstall on ${vm} timed out after ${AUTOINSTALL_TIMEOUT}s."
                log "  ${vm} running (autoinstall) — waiting 30s ..."
                sleep 30
                ;;
            *)
                log "  ${vm} state: '${STATE}' — waiting 10s ..."
                sleep 10
                ;;
        esac
    done

    local SSH_DEADLINE=$(( SECONDS + SSH_POLL_TIMEOUT ))
    until ssh_ready "${vm}" "${ip}"; do
        [[ ${SECONDS} -ge ${SSH_DEADLINE} ]] \
            && die "SSH on ${vm} not ready after ${SSH_POLL_TIMEOUT}s."
        log "  Waiting for SSH on ${vm} ..."
        sleep 5
    done
    log "✓  ${vm} SSH ready."
}

# ── Phase 1: Preflight ─────────────────────────────────────────────────────────

step "Phase 1: Preflight"

command -v cloud-localds &>/dev/null \
    || die "cloud-localds not found — run: sudo apt install cloud-image-utils"

command -v ansible-playbook &>/dev/null \
    || die "ansible-playbook not found — has the control_plane role been applied?"

[[ -f "${SSH_KEY}" ]] \
    || die "SSH key not found: ${SSH_KEY} — has the control_plane role been applied?"

[[ -f "${HOME}/.config/sops/age/keys.txt" ]] \
    || die "SOPS age key not found: ~/.config/sops/age/keys.txt"

ssh -o ConnectTimeout=5 -o BatchMode=yes \
    "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "echo ok" &>/dev/null \
    || die "Cannot reach hypervisor '${HYPERVISOR_ALIAS}' — has the handoff step run in bootstrap_saconsole.sh?"

remote "test -d '${REMOTE_IMAGES_DIR}'" \
    || die "${HYPERVISOR_ALIAS}:${REMOTE_IMAGES_DIR} not found — is the LUKS disk mounted?"

remote "virsh --connect qemu:///system pool-info esacp" &>/dev/null \
    || die "libvirt pool 'esacp' not active on ${HYPERVISOR_ALIAS}"

remote "test -f '${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}'" \
    || die "Ubuntu ISO not found on ${HYPERVISOR_ALIAS}: ${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}"

log "Preflight OK"

# ── Phase 2: Read saconsole SSH pubkey ─────────────────────────────────────────

step "Phase 2: Read saconsole SSH pubkey"

export CONTROLLER_PUBKEY
CONTROLLER_PUBKEY=$(cat "${SSH_KEY}.pub")
log "Controller pubkey: ${CONTROLLER_PUBKEY:0:40}..."

# ── Phase 3: Build seed ISOs ───────────────────────────────────────────────────

step "Phase 3: Build seed ISOs"

CLOUD_INIT_DIR="${SCRIPT_DIR}/cloud-init"
REMOTE_ISO="${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}"

for vm in "${TARGETS[@]}"; do
    TEMPLATE_DIR="${CLOUD_INIT_DIR}/toshiba-${vm}"
    SEED_ISO="${SCRIPT_DIR}/${vm}-toshiba-seed.iso"
    RENDERED_USERDATA="/tmp/${vm}-userdata-rendered.yml"

    [[ -f "${TEMPLATE_DIR}/user-data" ]] \
        || die "Missing cloud-init template: ${TEMPLATE_DIR}/user-data"
    [[ -f "${TEMPLATE_DIR}/meta-data" ]] \
        || die "Missing cloud-init template: ${TEMPLATE_DIR}/meta-data"

    # Inject saconsole's SSH pubkey into the user-data template
    envsubst < "${TEMPLATE_DIR}/user-data" > "${RENDERED_USERDATA}"

    if [[ -f "${SEED_ISO}" \
        && "${SEED_ISO}" -nt "${TEMPLATE_DIR}/user-data" \
        && "${SEED_ISO}" -nt "${TEMPLATE_DIR}/meta-data" ]]; then
        log "${vm}: seed ISO is current — skipping rebuild."
    else
        cloud-localds "${SEED_ISO}" "${RENDERED_USERDATA}" "${TEMPLATE_DIR}/meta-data"
        log "✓  ${SEED_ISO}"
    fi
    rm -f "${RENDERED_USERDATA}"
done

# ── Phase 4: Upload seed ISOs ──────────────────────────────────────────────────

step "Phase 4: Upload seed ISOs to ${HYPERVISOR_ALIAS}"

for vm in "${TARGETS[@]}"; do
    SEED_ISO="${SCRIPT_DIR}/${vm}-toshiba-seed.iso"
    REMOTE_SEED="${REMOTE_IMAGES_DIR}/${vm}-toshiba-seed.iso"
    LOCAL_MTIME=$(stat -c %Y "${SEED_ISO}")
    REMOTE_MTIME=$(remote "stat -c %Y '${REMOTE_SEED}' 2>/dev/null || echo 0")

    if [[ "${REMOTE_MTIME}" -ge "${LOCAL_MTIME}" ]]; then
        log "${vm}: remote seed ISO is current — skipping upload."
    else
        log "Uploading ${vm} seed ISO ..."
        scp "${SEED_ISO}" "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}:${REMOTE_SEED}"
        log "✓  Uploaded ${vm} seed ISO."
    fi
done

# ── Phase 5: Create VMs ────────────────────────────────────────────────────────

step "Phase 5: Create target VMs on ${HYPERVISOR_ALIAS}"

for vm in "${TARGETS[@]}"; do
    REMOTE_SEED="${REMOTE_IMAGES_DIR}/${vm}-toshiba-seed.iso"
    RAM="${TARGET_RAM[${vm}]}"

    if vm_exists "${vm}"; then
        log "VM '${vm}' already exists on ${HYPERVISOR_ALIAS} — skipping."
        continue
    fi

    log "Creating VM '${vm}' (${RAM}MB RAM) ..."
    # Note: --os-variant ubuntu20.04 is required on toshiba (Ubuntu 20.04 stock
    # osinfo-db tops out there; ubuntu22.04/24.04 are absent). See CLAUDE.md.
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" bash <<REMOTE
virt-install \
    --connect qemu:///system \
    --name ${vm} \
    --ram ${RAM} \
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
    log "✓  VM '${vm}' created."
done

# ── Phase 6: Wait for first boot + SSH ────────────────────────────────────────

step "Phase 6: Wait for VMs to be ready"

for vm in "${TARGETS[@]}"; do
    ip="${TARGET_IP[${vm}]}"
    log "Waiting for ${vm} (${ip}) ..."
    wait_for_vm "${vm}" "${ip}"
done

# ── Phase 7: Snapshot — Fresh Install ─────────────────────────────────────────

step "Phase 7: Snapshot '${SNAPSHOT_FRESH}'"

for vm in "${TARGETS[@]}"; do
    take_snapshot "${vm}" "${SNAPSHOT_FRESH}"
done

# ── Phase 8: Ansible provision targets ────────────────────────────────────────

step "Phase 8: Ansible provision targets"
log "Limit   : targets (Plays 1, 3, 4 — base config + saconsole pubkey + services)"
log "SSH key : ${SSH_KEY}"

export ANSIBLE_CONFIG="${ANSIBLE_DIR}/ansible.cfg"
export ANSIBLE_PRIVATE_KEY_FILE="${SSH_KEY}"

# Clear known_hosts entries for target IPs to avoid stale host key rejections
for vm in "${TARGETS[@]}"; do
    ip="${TARGET_IP[${vm}]}"
    ssh-keygen -R "${vm}" 2>/dev/null || true
    ssh-keygen -R "${ip}" 2>/dev/null || true
done

cd "${ANSIBLE_DIR}"
# --limit targets runs: Play 1 (base config), Play 3 (authorise saconsole), Play 4 (services).
# Play 2 (saconsole-only) and Play 5 (controller/localhost) are skipped automatically.
#
# Play 3 depends on hostvars['saconsole']['saconsole_ssh_pubkey']. Since we run
# --limit targets, saconsole's play does not execute and the fact is not populated.
# We pass the pubkey explicitly via saconsole_override_pubkey — Play 3 checks for
# this var before falling back to hostvars. See site-kvm.yml Play 3 comment.
#
# Use a temp YAML vars file so the SSH public key (which contains spaces) is
# preserved as a single value. Ansible's key=value --extra-vars splits on spaces.
TMPVARS=$(mktemp /tmp/ansible-vars-XXXXXX.yml)
trap "rm -f ${TMPVARS}" EXIT
cat > "${TMPVARS}" << ENDVARS
saconsole_override_pubkey: "$(cat ${SSH_KEY}.pub)"
ansible_ssh_private_key_file: "${SSH_KEY}"
ENDVARS

ansible-playbook \
    -i inventory/kvm.yml \
    site-kvm.yml \
    --limit targets \
    --extra-vars "@${TMPVARS}"

log "Ansible provision complete."

# ── Phase 9: Snapshot — Stage 2.2 Targets Baseline ───────────────────────────

step "Phase 9: Snapshot '${SNAPSHOT_BASELINE}'"

for vm in "${TARGETS[@]}"; do
    take_snapshot "${vm}" "${SNAPSHOT_BASELINE}"
done

# ── Done ──────────────────────────────────────────────────────────────────────

step "Done"
cat <<SUMMARY

  target1 and target2 provisioned on ${HYPERVISOR_ALIAS}.
  Snapshots: '${SNAPSHOT_FRESH}', '${SNAPSHOT_BASELINE}'

  ── Services ──────────────────────────────────────────────────────────────
  MariaDB:       target1 (10.10.0.3:3306 internal), target2 (10.10.0.4:3306 internal)
  MariaDB MCP:   http://10.10.0.3:9001/sse  and  http://10.10.0.4:9001/sse
  Nginx UI HTTP: http://10.10.0.3:80        and  http://10.10.0.4:80
  Nginx UI MCP:  http://10.10.0.3:9000/mcp?node_secret=<NGINX_UI_NODE_SECRET>
                 http://10.10.0.4:9000/mcp?node_secret=<NGINX_UI_NODE_SECRET>
  node_exporter: http://10.10.0.3:9100      and  http://10.10.0.4:9100

  ── Next steps ──────────────────────────────────────────────────────────
  1. Verify WireGuard mesh (from controller):
       python tools/esacp.py verifyVPN

  2. Validate observability stack:
       python tools/esacp.py validateObservability

  3. Add MCP servers to Claude Code settings (~/.claude/settings.json):
       "mcpServers": {
         "grafana": {
           "type": "sse",
           "url": "http://10.10.0.1:8000/sse"
         },
         "mariadb-target1": {
           "type": "sse",
           "url": "http://10.10.0.3:9001/sse"
         },
         "mariadb-target2": {
           "type": "sse",
           "url": "http://10.10.0.4:9001/sse"
         },
         "nginx-target1": {
           "type": "sse",
           "url": "http://10.10.0.3:9000/mcp?node_secret=<NGINX_UI_NODE_SECRET>"
         },
         "nginx-target2": {
           "type": "sse",
           "url": "http://10.10.0.4:9000/mcp?node_secret=<NGINX_UI_NODE_SECRET>"
         }
       }
     Replace <NGINX_UI_NODE_SECRET> with the value of nginx_ui_node_secret
     from ansible/group_vars/all.sops.yml (or the default if not overridden).

SUMMARY
