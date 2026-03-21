#!/usr/bin/env bash
# prepare_hypervisor.sh — Check and prepare a bare KVM hypervisor host + controller
#
# Run from the project root on the CONTROLLER before running bootstrap_saconsole.sh.
# Controller-side tools are auto-installed where possible.
# Hypervisor-side checks report pass/fail with exact fix commands — they do not
# apply changes over SSH (no sudo over BatchMode).
#
# Usage:
#   bash platforms/kvm/prepare_hypervisor.sh
#
# Sections:
#   1. Controller prereqs  (local — auto-install where safe)
#   2. Hypervisor SSH auth (batch mode — MANUAL if not yet set up)
#   3. Hypervisor state    (via SSH — check + fix guidance only)
#   4. Post-bootstrap      (iptables port-forward — guidance only)
#
# After all checks pass, bootstrap_saconsole.sh preflight will succeed.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ANSIBLE_DIR="${PROJ_ROOT}/ansible"

# ── Configuration (must match bootstrap_saconsole.sh) ─────────────────────────

HYPERVISOR_ALIAS="toshy"
HYPERVISOR_USER="hasan"
HYPERVISOR_LAN_IP="192.168.40.16"
REMOTE_MOUNT_POINT="/mnt/esacp-disk"
REMOTE_IMAGES_DIR="${REMOTE_MOUNT_POINT}/var/lib/libvirt/images"
UBUNTU_ISO_NAME="ubuntu-24.04.4-live-server-amd64.iso"
UBUNTU_ISO_URL="https://releases.ubuntu.com/24.04.4/${UBUNTU_ISO_NAME}"
SSH_KEY="${HOME}/.ssh/hasan_mighty"
LIBVIRT_POOL="esacp"

# ── Output helpers ─────────────────────────────────────────────────────────────

PASS=0; FAIL=0; WARN=0; MANUAL_COUNT=0

ok()      { echo "  ✅  $*";           PASS=$((PASS+1)); }
applied() { echo "  🔧  $* — applied"; PASS=$((PASS+1)); }
fail()    { echo "  ❌  $*";           FAIL=$((FAIL+1)); }
warn()    { echo "  ⚠️   $*";           WARN=$((WARN+1)); }
manual()  { echo "  👤  [MANUAL] $*";  MANUAL_COUNT=$((MANUAL_COUNT+1)); }
hdr()     { echo ""; echo "── $* ──────────────────────────────────────────"; }
fix()     { echo "      Fix: $*"; }
info()    { echo "      ℹ   $*"; }

remote() {
    ssh -o ConnectTimeout=5 -o BatchMode=yes \
        "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"
}

# ── Header ─────────────────────────────────────────────────────────────────────

echo ""
echo "ESACP — Prepare KVM Hypervisor Host"
echo "===================================="
echo "  Controller : ${HOSTNAME}"
echo "  Hypervisor : ${HYPERVISOR_ALIAS} (${HYPERVISOR_USER}@${HYPERVISOR_LAN_IP})"

# ── Part 1: Controller prereqs ─────────────────────────────────────────────────

hdr "1. Controller — SSH keypair"

if [[ -f "${SSH_KEY}" ]]; then
    ok "SSH keypair present: ${SSH_KEY}"
else
    ssh-keygen -t ed25519 -f "${SSH_KEY}" -C "${USER}@${HOSTNAME}" -N "" &>/dev/null \
        && applied "SSH keypair generated: ${SSH_KEY}" \
        || { fail "Failed to generate SSH keypair at ${SSH_KEY}"; }
fi

# ── SSH alias check ────────────────────────────────────────────────────────────
hdr "1b. Controller — SSH alias"

if ssh -G "${HYPERVISOR_ALIAS}" &>/dev/null 2>&1 | grep -q hostname \
   || ssh -G "${HYPERVISOR_ALIAS}" 2>/dev/null | grep -qi "hostname ${HYPERVISOR_LAN_IP}\|hostname toshiba"; then
    ok "SSH alias '${HYPERVISOR_ALIAS}' configured in ~/.ssh/config"
else
    # A simpler check: does 'ssh -G toshy' resolve to the right host?
    _resolved=$(ssh -G "${HYPERVISOR_ALIAS}" 2>/dev/null | awk '/^hostname /{print $2}')
    if [[ -n "${_resolved}" ]]; then
        ok "SSH alias '${HYPERVISOR_ALIAS}' → ${_resolved}"
    else
        fail "SSH alias '${HYPERVISOR_ALIAS}' not found in ~/.ssh/config"
        fix "Add to ~/.ssh/config:"
        info "  Host ${HYPERVISOR_ALIAS}"
        info "    User ${HYPERVISOR_USER}"
        info "    HostName ${HYPERVISOR_LAN_IP}"
        info "    IdentityFile ${SSH_KEY}"
        info "    ServerAliveInterval 120"
        info "    ServerAliveCountMax 20"
    fi
fi

# ── cloud-image-utils ──────────────────────────────────────────────────────────
hdr "1c. Controller — cloud-image-utils"

if command -v cloud-localds &>/dev/null; then
    ok "cloud-localds present"
else
    echo "  Installing cloud-image-utils ..."
    sudo apt-get install -y -q cloud-image-utils 2>&1 | tail -1
    command -v cloud-localds &>/dev/null \
        && applied "cloud-image-utils installed" \
        || fail "cloud-image-utils install failed — run: sudo apt install cloud-image-utils"
fi

# ── sops ──────────────────────────────────────────────────────────────────────
hdr "1d. Controller — sops"

if command -v sops &>/dev/null; then
    ok "sops: $(sops --version --check-for-updates 2>/dev/null | head -1)"
else
    fail "sops not found at /usr/local/bin/sops"
    fix "Download from https://github.com/getsops/sops/releases"
    info "sudo install -m755 sops-v<version>.linux.amd64 /usr/local/bin/sops"
fi

# ── age ───────────────────────────────────────────────────────────────────────
hdr "1e. Controller — age"

if command -v age &>/dev/null; then
    ok "age: $(age --version 2>/dev/null)"
else
    fail "age not found at /usr/local/bin/age"
    fix "Download from https://github.com/FiloSottile/age/releases"
    info "sudo install -m755 age /usr/local/bin/age"
fi

# ── SOPS age key ──────────────────────────────────────────────────────────────
hdr "1f. Controller — SOPS age key"

if [[ -f "${HOME}/.config/sops/age/keys.txt" ]]; then
    ok "Age key present: ~/.config/sops/age/keys.txt"
else
    fail "Age key not found: ~/.config/sops/age/keys.txt"
    fix "Place the project age private key at that path (mode 0600)"
    info "mkdir -p ~/.config/sops/age && chmod 700 ~/.config/sops/age"
    info "# copy the key file, then: chmod 600 ~/.config/sops/age/keys.txt"
fi

# ── Ansible ───────────────────────────────────────────────────────────────────
hdr "1g. Controller — Ansible"

if command -v ansible-playbook &>/dev/null; then
    ok "ansible-playbook: $(ansible --version 2>/dev/null | head -1)"
else
    echo "  Installing Ansible ..."
    sudo apt-get install -y -q ansible 2>&1 | tail -1
    command -v ansible-playbook &>/dev/null \
        && applied "Ansible installed" \
        || fail "Ansible install failed — run: sudo apt install ansible"
fi

# ── Ansible collections ───────────────────────────────────────────────────────
hdr "1h. Controller — Ansible collections"

_missing_collections=()
for col in community.sops community.general community.crypto community.docker ansible.posix; do
    ansible-galaxy collection list 2>/dev/null | grep -q "${col}" \
        || _missing_collections+=("${col}")
done

if [[ ${#_missing_collections[@]} -eq 0 ]]; then
    ok "All required Ansible collections installed"
else
    echo "  Installing missing collections: ${_missing_collections[*]} ..."
    ansible-galaxy collection install -r "${ANSIBLE_DIR}/requirements.yml" -q 2>&1 | tail -3
    _still_missing=()
    for col in "${_missing_collections[@]}"; do
        ansible-galaxy collection list 2>/dev/null | grep -q "${col}" \
            || _still_missing+=("${col}")
    done
    if [[ ${#_still_missing[@]} -eq 0 ]]; then
        applied "Ansible collections installed"
    else
        fail "Could not install: ${_still_missing[*]}"
        fix "ansible-galaxy collection install -r ansible/requirements.yml"
    fi
fi

# ── github-mcp-server ─────────────────────────────────────────────────────────
hdr "1i. Controller — github-mcp-server"

GITHUB_MCP_BIN="/usr/local/bin/github-mcp-server"
if [[ -x "${GITHUB_MCP_BIN}" ]]; then
    _ghver=$("${GITHUB_MCP_BIN}" --version 2>/dev/null | awk '/Version:/{print $2}')
    ok "github-mcp-server ${_ghver}"
else
    fail "github-mcp-server not found at ${GITHUB_MCP_BIN}"
    fix "Download from https://github.com/github/github-mcp-server/releases"
    info "cd /tmp && curl -sL <Linux_x86_64.tar.gz URL> | tar -xz"
    info "sudo install -m755 /tmp/github-mcp-server /usr/local/bin/github-mcp-server"
fi

# ── ESACP repo ────────────────────────────────────────────────────────────────
hdr "1j. Controller — ESACP repo"


if [[ -f "${PROJ_ROOT}/hosts_map.yml" ]]; then
    ok "ESACP repo present: ${PROJ_ROOT}"
else
    fail "hosts_map.yml not found — repo may not be fully cloned"
    fix "git clone https://github.com/martinhbramwell/ESACP.git ~/projects/Logichem/ESACP"
fi

# ── Part 2: Hypervisor SSH auth ────────────────────────────────────────────────

hdr "2. Hypervisor — SSH auth"

hypervisor_reachable=false
if remote "echo ok" &>/dev/null; then
    ok "SSH batch auth works: ${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}"
    hypervisor_reachable=true
else
    manual "SSH key auth not yet established — one password session required:"
    info "ssh-copy-id -i ${SSH_KEY}.pub ${HYPERVISOR_USER}@${HYPERVISOR_LAN_IP}"
    info "Then re-run this script to complete hypervisor checks."
fi

# ── Part 3: Hypervisor state ───────────────────────────────────────────────────

if ! "${hypervisor_reachable}"; then
    echo ""
    echo "  Skipping hypervisor checks — SSH auth not established (see Part 2)."
else

hdr "3a. Hypervisor — hostname"
_hv_hostname=$(remote hostname 2>/dev/null || echo "")
if [[ -n "${_hv_hostname}" ]]; then
    ok "Hostname: ${_hv_hostname}"
    [[ "${_hv_hostname}" == "toshiba" ]] || warn "Hostname is '${_hv_hostname}' — expected 'toshiba'"
else
    fail "Could not retrieve hostname"
fi

hdr "3b. Hypervisor — SSH daemon"
if remote systemctl is-active ssh &>/dev/null; then
    ok "SSH daemon active"
else
    fail "SSH daemon not active"
    fix "On hypervisor: sudo systemctl enable --now ssh"
fi

hdr "3c. Hypervisor — KVM / libvirt packages"
# Check by command presence (package names differ between Ubuntu versions:
# virt-install binary comes from 'virtinst' on Ubuntu 20.04, 'virt-manager' on others)
_kvm_ok=true
for cmd in virsh virt-install; do
    remote "command -v ${cmd}" &>/dev/null \
        || { fail "Command not found on hypervisor: ${cmd}"; _kvm_ok=false; }
done
if "${_kvm_ok}"; then
    _virsh_ver=$(remote virsh --connect qemu:///system version 2>/dev/null \
        | awk '/Using library/{print $NF}')
    ok "KVM/libvirt commands present (libvirt ${_virsh_ver})"
else
    fix "On hypervisor: sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients virt-install"
fi

hdr "3d. Hypervisor — libvirtd"
if remote systemctl is-active libvirtd &>/dev/null; then
    ok "libvirtd active"
else
    fail "libvirtd not active"
    fix "On hypervisor: sudo systemctl enable --now libvirtd"
fi

hdr "3e. Hypervisor — libvirt group membership"
if remote groups "${HYPERVISOR_USER}" 2>/dev/null | grep -q libvirt; then
    ok "${HYPERVISOR_USER} is in libvirt group"
else
    fail "${HYPERVISOR_USER} not in libvirt group"
    fix "On hypervisor: sudo usermod -aG libvirt ${HYPERVISOR_USER}"
    manual "Log out and back in on the hypervisor after adding to group"
fi

hdr "3f. Hypervisor — default libvirt network"
_net_state=$(remote virsh --connect qemu:///system net-list 2>/dev/null \
    | awk '/default/{print $2}')
if [[ "${_net_state}" == "active" ]]; then
    ok "Default libvirt network active"
else
    fail "Default libvirt network not active (state: '${_net_state:-not found}')"
    fix "On hypervisor: virsh --connect qemu:///system net-autostart default"
    fix "              virsh --connect qemu:///system net-start default"
fi

hdr "3g. Hypervisor — LUKS disk mounted"
if remote mountpoint "${REMOTE_MOUNT_POINT}" &>/dev/null; then
    ok "LUKS disk mounted: ${REMOTE_MOUNT_POINT}"
else
    fail "LUKS disk not mounted at ${REMOTE_MOUNT_POINT}"
    manual "Unlock and mount the LUKS disk on the hypervisor (requires passphrase)"
    info "sudo cryptsetup open /dev/<disk> esacp-disk"
    info "sudo mount /dev/mapper/esacp-disk /mnt/esacp-disk"
    info "Or add to /etc/crypttab + /etc/fstab for auto-mount with passphrase prompt at boot"
fi

hdr "3h. Hypervisor — libvirt pool '${LIBVIRT_POOL}'"
_pool_state=$(remote virsh --connect qemu:///system pool-info "${LIBVIRT_POOL}" 2>/dev/null \
    | awk '/^State:/{print $2}')
if [[ "${_pool_state}" == "running" ]]; then
    _pool_free=$(remote virsh --connect qemu:///system pool-info "${LIBVIRT_POOL}" 2>/dev/null \
        | awk '/^Available:/{print $2, $3}')
    ok "libvirt pool '${LIBVIRT_POOL}' running (${_pool_free} free)"
else
    fail "libvirt pool '${LIBVIRT_POOL}' not running (state: '${_pool_state:-not found}')"
    fix "On hypervisor (after mounting LUKS disk):"
    info "virsh --connect qemu:///system pool-define-as ${LIBVIRT_POOL} dir \\"
    info "    --target ${REMOTE_IMAGES_DIR}"
    info "virsh --connect qemu:///system pool-start ${LIBVIRT_POOL}"
    info "virsh --connect qemu:///system pool-autostart ${LIBVIRT_POOL}"
fi

hdr "3i. Hypervisor — Ubuntu installation ISO"
if remote test -f "${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}" 2>/dev/null; then
    ok "Ubuntu ISO present: ${UBUNTU_ISO_NAME}"
else
    fail "Ubuntu ISO not found: ${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}"
    fix "On hypervisor (after mounting LUKS disk):"
    info "cd ${REMOTE_IMAGES_DIR}"
    info "wget ${UBUNTU_ISO_URL}"
fi

fi  # end hypervisor_reachable block

# ── Part 4: Post-bootstrap guidance ───────────────────────────────────────────

hdr "4. Post-bootstrap — WireGuard port-forward"
echo ""
echo "  After bootstrap_saconsole.sh completes, Mighty's WireGuard spoke needs"
echo "  to reach saconsole (192.168.122.10:51820) through the hypervisor."
echo "  Run these two iptables rules on the hypervisor (replace wlp2s0 with"
echo "  the actual LAN interface: \`ip route get 1 | awk '{print \$5; exit}'\`):"
echo ""
echo "    sudo iptables -t nat -A PREROUTING -i wlp2s0 -p udp --dport 51820 \\"
echo "        -j DNAT --to-destination 192.168.122.10:51820"
echo "    sudo iptables -I FORWARD 1 -i wlp2s0 -o virbr0 -p udp \\"
echo "        -d 192.168.122.10 --dport 51820 -j ACCEPT"
echo ""
echo "  Note: these rules are not persistent across reboots (Stage 2.x work)."

# ── Summary ────────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
printf "  ✅ Passed: %-4s ⚠️  Warnings: %-4s ❌ Failed: %-4s 👤 Manual: %s\n" \
    "${PASS}" "${WARN}" "${FAIL}" "${MANUAL_COUNT}"
echo "═══════════════════════════════════════════════════════"
echo ""

if [[ ${FAIL} -gt 0 ]]; then
    echo "❌  Fix all failures before running bootstrap_saconsole.sh."
    exit 1
elif [[ ${MANUAL_COUNT} -gt 0 ]]; then
    echo "👤  Complete [MANUAL] steps above, then re-run to confirm."
    exit 0
else
    echo "✅  Controller and hypervisor ready. Run bootstrap_saconsole.sh."
    exit 0
fi
