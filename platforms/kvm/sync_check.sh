#!/usr/bin/env bash
# sync_check.sh — KVM/Xubuntu (Mighty) platform sync check
#
# Run at the start of every session before doing any other work.
# Objective: verify the toshiba-hosted ESACP estate matches expected state.
# If any check fails, fix it before proceeding.
#
# Usage (from project root or any directory):
#   bash platforms/kvm/sync_check.sh
#
# Sections:
#   1.  Git state
#   2.  Local tooling (SOPS/age, Ansible, virsh)
#   3.  SSH keys
#   4.  SOPS decryption
#   5.  toshiba reachability
#   6.  toshiba — LUKS disk + libvirt pool
#   7.  VMs on toshiba (saconsole, target1, target2)
#   8.  WireGuard — local interface + handshake
#   9.  WireGuard mesh — ping all peers
#  10.  Observability stack (saconsole)
#  11.  Target stacks (target1, target2)
#  12.  MCP endpoints
#  13.  GitHub MCP server (binary + settings.json)

PASS=0; FAIL=0; WARN=0

ok()   { echo "  ✅  $*"; PASS=$((PASS+1)); }
fail() { echo "  ❌  $*"; FAIL=$((FAIL+1)); }
warn() { echo "  ⚠️   $*"; WARN=$((WARN+1)); }
hdr()  { echo ""; echo "── $* ──────────────────────────────────────────"; }
fix()  { echo "      Fix: $*"; }

PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ANSIBLE_DIR="${PROJ_ROOT}/ansible"

HYPERVISOR_ALIAS="toshiba"
HYPERVISOR_USER="hasan"

SACONSOLE_IP="192.168.122.10"
TARGET1_IP="192.168.122.11"
TARGET2_IP="192.168.122.12"

WG_HUB="10.10.0.1"
WG_TARGET1="10.10.0.3"
WG_TARGET2="10.10.0.4"

MCP_GRAFANA="http://10.10.0.1:8000/sse"
MCP_MARIADB_T1="http://10.10.0.3:9001/sse"
MCP_MARIADB_T2="http://10.10.0.4:9001/sse"
MCP_NGINX_T1="http://10.10.0.3:9000/mcp?node_secret=esacp_node_secret_changeme"
MCP_NGINX_T2="http://10.10.0.4:9000/mcp?node_secret=esacp_node_secret_changeme"

remote_toshiba() { ssh -o ConnectTimeout=5 -o BatchMode=yes \
    "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" "$@"; }

remote_saconsole() { ssh -o ConnectTimeout=5 -o BatchMode=yes \
    -o ProxyJump="${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
    you@"${SACONSOLE_IP}" "$@"; }

echo ""
echo "ESACP KVM Platform (Mighty → toshiba) — Sync Check"
echo "==================================================="

# ── 1. Git ────────────────────────────────────────────────────────────────────
hdr "1. Git"

cd "${PROJ_ROOT}"

BRANCH=$(git rev-parse --abbrev-ref HEAD)
[[ "${BRANCH}" == "main" ]] && ok "On main branch" \
    || warn "On branch '${BRANCH}' — expected main"

git fetch --quiet origin 2>/dev/null
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "unknown")
[[ "${LOCAL}" == "${REMOTE}" ]] && ok "Up to date with origin/main" \
    || warn "Local differs from origin/main — pull or push needed"

DIRTY=$(git status --porcelain)
if [[ -z "${DIRTY}" ]]; then
    ok "Working tree clean"
else
    warn "Uncommitted changes present"
    git status --short
fi

# ── 2. Local tooling ──────────────────────────────────────────────────────────
hdr "2. Local tooling"

command -v ansible-playbook &>/dev/null \
    && ok "ansible-playbook: $(ansible --version | head -1)" \
    || fail "ansible-playbook not found — install Ansible"

if command -v sops &>/dev/null; then
    _sops_out=$(sops --version --check-for-updates 2>/dev/null)
    ok "sops: $(echo "$_sops_out" | head -1)"
    _sops_update=$(echo "$_sops_out" | grep -i 'new version' | sed 's/^\[info\] //' || true)
    [[ -n "$_sops_update" ]] && warn "sops update available — $_sops_update" \
        && fix "https://github.com/getsops/sops/releases"
else
    fail "sops not found — install sops (see SETUP_GUIDE.md)"
fi

command -v virsh &>/dev/null \
    && ok "virsh available (local KVM tools present)" \
    || warn "virsh not found — local KVM management unavailable"

[[ -f "${ANSIBLE_DIR}/ansible.cfg" ]] \
    && ok "ansible/ansible.cfg present" \
    || fail "ansible/ansible.cfg missing"

grep -q "community.sops.sops" "${ANSIBLE_DIR}/ansible.cfg" 2>/dev/null \
    && ok "ansible.cfg: community.sops vars plugin enabled" \
    || { fail "ansible.cfg missing community.sops vars plugin — SOPS secrets will be undefined"
         fix "Add to ansible.cfg [defaults]: vars_plugins_enabled = host_group_vars,community.sops.sops"; }

# ── 3. SSH keys ───────────────────────────────────────────────────────────────
hdr "3. SSH keys"

[[ -f "${HOME}/.ssh/hasan_mighty" ]] \
    && ok "~/.ssh/hasan_mighty present (KVM Ansible key)" \
    || fail "~/.ssh/hasan_mighty missing — Ansible KVM plays will fail"

# Check toshy SSH alias is configured
ssh -o ConnectTimeout=1 -o BatchMode=yes -o StrictHostKeyChecking=no \
    "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" true 2>/dev/null \
    && ok "SSH alias 'toshiba' resolves and key auth works" \
    || fail "Cannot reach toshiba via SSH alias — check ~/.ssh/config and authorized_keys"

# ── 4. SOPS decryption ────────────────────────────────────────────────────────
hdr "4. SOPS / age"

[[ -f "${HOME}/.config/sops/age/keys.txt" ]] \
    && ok "Age key present at ~/.config/sops/age/keys.txt" \
    || fail "Age key missing — SOPS decryption will fail (see SETUP_GUIDE.md)"

sops -d "${PROJ_ROOT}/config/wireguard/keys.sops.yml" &>/dev/null \
    && ok "config/wireguard/keys.sops.yml decrypts OK" \
    || fail "keys.sops.yml decryption failed — WireGuard key deployment will fail"

sops -d "${ANSIBLE_DIR}/group_vars/all.sops.yml" &>/dev/null \
    && ok "ansible/group_vars/all.sops.yml decrypts OK" \
    || fail "all.sops.yml decryption failed — secrets (Telegram, Grafana, nginx) will be undefined"

# ── 5. toshiba reachability ───────────────────────────────────────────────────
hdr "5. toshiba reachability"

if remote_toshiba "echo ok" &>/dev/null; then
    ok "SSH to toshiba (${HYPERVISOR_ALIAS}) — connected"
    TOSHIBA_UP=true
else
    fail "Cannot SSH to toshiba — all downstream checks will be skipped"
    TOSHIBA_UP=false
fi

# ── 6. toshiba — LUKS disk + libvirt pool ─────────────────────────────────────
hdr "6. toshiba — disk + libvirt pool"

if [[ "${TOSHIBA_UP}" == true ]]; then
    remote_toshiba "mountpoint -q /mnt/esacp-disk" \
        && ok "/mnt/esacp-disk is mounted" \
        || { fail "/mnt/esacp-disk NOT mounted — all VM images are unavailable"
             fix "On toshiba: sudo cryptsetup luksOpen /dev/sdX esacp-disk && sudo mount /mnt/esacp-disk"
             fix "Or reboot toshiba and enter LUKS passphrase at prompt"; }

    remote_toshiba "virsh --connect qemu:///system pool-info esacp" &>/dev/null \
        && ok "libvirt pool 'esacp' is active" \
        || { fail "libvirt pool 'esacp' not active on toshiba"
             fix "On toshiba: virsh --connect qemu:///system pool-start esacp"; }
fi

# ── 7. VMs on toshiba ─────────────────────────────────────────────────────────
hdr "7. VMs on toshiba"

if [[ "${TOSHIBA_UP}" == true ]]; then
    for vm in saconsole target1 target2; do
        STATE=$(remote_toshiba "virsh --connect qemu:///system domstate ${vm} 2>/dev/null" \
            | tr -d '\n' || echo "unknown")
        if [[ "${STATE}" == "running" ]]; then
            ok "VM '${vm}' — running"
        elif [[ "${STATE}" == "shut off" ]]; then
            fail "VM '${vm}' — shut off"
            fix "On toshiba: virsh --connect qemu:///system start ${vm}"
        else
            warn "VM '${vm}' — state: '${STATE}'"
        fi
    done
fi

# ── 8. WireGuard — local interface + handshake ────────────────────────────────
hdr "8. WireGuard (Mighty wg0)"

if ip link show wg0 &>/dev/null; then
    WG_ADDR=$(ip -4 addr show wg0 2>/dev/null | awk '/inet /{print $2}')
    ok "wg0 is UP — address: ${WG_ADDR:-unknown}"
else
    fail "wg0 interface not found"
    fix "sudo wg-quick up wg0  OR  sudo systemctl start wg-quick@wg0"
fi

# Check recency of handshake (wg show dump gives Unix timestamps)
WG_DUMP=$(sudo -n wg show wg0 dump 2>/dev/null || true)
if [[ -n "${WG_DUMP}" ]]; then
    HS_TS=$(echo "${WG_DUMP}" | awk 'NR>1{print $5}' | head -1)
    NOW=$(date +%s)
    AGE=$(( NOW - HS_TS ))
    if [[ ${HS_TS} -eq 0 ]]; then
        warn "wg0: no handshake yet with saconsole hub"
        fix "Check toshiba iptables DNAT rule for UDP 51820 is still in place"
    elif [[ ${AGE} -lt 180 ]]; then
        ok "wg0: handshake with saconsole ${AGE}s ago (healthy)"
    elif [[ ${AGE} -lt 600 ]]; then
        warn "wg0: last handshake ${AGE}s ago — stale (expected <180s with keepalive=25s)"
        fix "Check toshiba iptables port-forward: sudo iptables -t nat -L PREROUTING -n"
    else
        fail "wg0: no handshake in ${AGE}s — WireGuard tunnel is down"
        fix "Check toshiba iptables port-forward and saconsole wg0 status"
    fi
else
    warn "Could not read wg0 dump (sudo may be required) — skipping handshake age check"
fi

# ── 9. WireGuard mesh — ping all peers ────────────────────────────────────────
hdr "9. WireGuard mesh"

for label_ip in "saconsole:${WG_HUB}" "target1:${WG_TARGET1}" "target2:${WG_TARGET2}"; do
    label="${label_ip%%:*}"
    ip="${label_ip##*:}"
    if ping -c1 -W2 "${ip}" &>/dev/null; then
        ok "Ping ${label} (${ip}) — reachable"
    else
        fail "Ping ${label} (${ip}) — unreachable"
        fix "Check wg0 handshake and that ${label} VM is running on toshiba"
    fi
done

# ── 10. Observability stack — saconsole ───────────────────────────────────────
hdr "10. Observability stack (saconsole)"

SACONSOLE_REACHABLE=false
if ping -c1 -W2 "${WG_HUB}" &>/dev/null; then
    SACONSOLE_REACHABLE=true
fi

if [[ "${SACONSOLE_REACHABLE}" == true ]]; then
    OBS_CONTAINERS=$(remote_saconsole \
        "docker ps --format '{{.Names}}:{{.Status}}'" 2>/dev/null || true)

    for svc in prometheus grafana loki promtail alertmanager node_exporter cadvisor mcp-grafana; do
        ROW=$(echo "${OBS_CONTAINERS}" | grep "^${svc}:" || true)
        if [[ -z "${ROW}" ]]; then
            fail "saconsole: '${svc}' container not running"
            fix "SSH to saconsole and run: docker-compose -f /opt/observability/docker-compose.yml up -d ${svc}"
        elif echo "${ROW}" | grep -qi "unhealthy\|restarting\|exited"; then
            warn "saconsole: '${svc}' — $(echo "${ROW}" | cut -d: -f2-)"
        else
            ok "saconsole: '${svc}' — up"
        fi
    done
else
    warn "saconsole unreachable over WireGuard — skipping observability checks"
fi

# ── 11. Target stacks ─────────────────────────────────────────────────────────
hdr "11. Target stacks"

for target_label_ip in "target1:${WG_TARGET1}:${TARGET1_IP}" \
                       "target2:${WG_TARGET2}:${TARGET2_IP}"; do
    target="${target_label_ip%%:*}"
    rest="${target_label_ip#*:}"
    wg_ip="${rest%%:*}"
    virbr_ip="${rest##*:}"

    if ! ping -c1 -W2 "${wg_ip}" &>/dev/null; then
        warn "${target} (${wg_ip}) unreachable over WireGuard — skipping stack check"
        continue
    fi

    TARGET_CONTAINERS=$(remote_saconsole \
        "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 you@${virbr_ip} \
         'docker ps --format \"{{.Names}}:{{.Status}}\"'" 2>/dev/null || true)

    for svc in mariadb mysqld_exporter mariadb_mcp nginx-ui; do
        ROW=$(echo "${TARGET_CONTAINERS}" | grep "^${svc}:" || true)
        if [[ -z "${ROW}" ]]; then
            fail "${target}: '${svc}' container not running"
            fix "SSH to ${target} and run: docker-compose -f /opt/mariadb/docker-compose.yml up -d  (or /opt/nginx-ui/)"
        elif echo "${ROW}" | grep -qi "unhealthy\|restarting\|exited"; then
            warn "${target}: '${svc}' — $(echo "${ROW}" | cut -d: -f2-)"
        else
            ok "${target}: '${svc}' — up"
        fi
    done
done

# ── 12. MCP endpoints ─────────────────────────────────────────────────────────
hdr "12. MCP endpoints"

for label_url in \
    "grafana-mcp:${MCP_GRAFANA}" \
    "mariadb-target1:${MCP_MARIADB_T1}" \
    "mariadb-target2:${MCP_MARIADB_T2}" \
    "nginx-target1:${MCP_NGINX_T1}" \
    "nginx-target2:${MCP_NGINX_T2}"; do

    label="${label_url%%:http*}"
    url="${label_url#*:http}"
    url="http${url}"

    # SSE endpoints keep the connection open — curl exits 28 (timeout) after
    # receiving the HTTP 200 header. Use '; true' to suppress the non-zero
    # exit without appending a fallback string to the captured HTTP code.
    HTTP_CODE=$(curl -s --max-time 5 "${url}" -o /dev/null -w "%{http_code}" 2>/dev/null; true)
    [[ -z "${HTTP_CODE}" ]] && HTTP_CODE="000"
    if [[ "${HTTP_CODE}" == "200" ]]; then
        ok "MCP ${label} — HTTP ${HTTP_CODE}"
    elif [[ "${HTTP_CODE}" == "000" ]]; then
        fail "MCP ${label} — unreachable (timeout/refused)"
        fix "Check that the container is running and UFW allows saconsole WG IP"
    else
        warn "MCP ${label} — HTTP ${HTTP_CODE} (unexpected)"
    fi
done

# ── 13. GitHub MCP server ─────────────────────────────────────────────────────
hdr "13. GitHub MCP server"

GITHUB_MCP_BIN="/usr/local/bin/github-mcp-server"
if [[ -x "${GITHUB_MCP_BIN}" ]]; then
    _ghver=$("${GITHUB_MCP_BIN}" --version 2>/dev/null | awk '/Version:/{print $2}')
    ok "github-mcp-server ${_ghver} present"
else
    fail "github-mcp-server not found at ${GITHUB_MCP_BIN}"
    fix "bash platforms/kvm/prepare_hypervisor.sh (or install manually from github/github-mcp-server releases)"
fi

if grep -q 'github-mcp-server' "${HOME}/.claude/settings.json" 2>/dev/null; then
    ok "github MCP entry present in ~/.claude/settings.json"
else
    fail "github MCP not configured in ~/.claude/settings.json"
    fix "Add github-mcp-server entry (type: stdio) with GITHUB_PERSONAL_ACCESS_TOKEN"
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
printf "  ✅ Passed: %-4s  ⚠️  Warnings: %-4s  ❌ Failed: %s\n" \
    "${PASS}" "${WARN}" "${FAIL}"
echo "═══════════════════════════════════════════════════════"
echo ""

if [[ ${FAIL} -gt 0 ]]; then
    echo "❌  Fix all failures before starting work."
    exit 1
elif [[ ${WARN} -gt 0 ]]; then
    echo "⚠️   Warnings present — review before proceeding."
    exit 0
else
    echo "✅  Environment clean. Safe to start a new session."
    exit 0
fi
