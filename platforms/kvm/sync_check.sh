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
#   7.  VMs on toshiba (derived from hosts_map.yml)
#   8.  WireGuard — local interface + handshake
#   9.  WireGuard mesh — ping all peers (derived from hosts_map.yml)
#  10.  Observability stack (saconsole)
#  11.  ERPNext sites — HTTPS reachability (derived from hosts_map.yml)
#  12.  MCP endpoints — all SSE servers in ~/.claude/settings.json
#  13.  GitHub MCP server (binary + settings.json + token)
#  14.  Cloudflare MCP (binary path, cf-mcp-refresh functional test)
#  15.  Telegram notification channel (bot token + API reachability)
#  16.  Cytoscape prototype API (localhost:8088)

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
    TOSHIBA_VMS=$(python3 - "${PROJ_ROOT}/hosts_map.yml" <<'PYEOF'
import yaml, sys
d = yaml.safe_load(open(sys.argv[1]))
for name, h in d.get('groups', {}).get('kvm', {}).items():
    if h.get('hypervisor') == 'toshiba':
        print(name)
PYEOF
)
    for vm in ${TOSHIBA_VMS}; do
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

WG_PEERS=$(python3 - "${PROJ_ROOT}/hosts_map.yml" <<'PYEOF'
import yaml, sys
d = yaml.safe_load(open(sys.argv[1]))
for name, h in d.get('groups', {}).get('kvm', {}).items():
    wg = h.get('wg_ip', '')
    if wg:
        print(f'{name}:{wg}')
PYEOF
)
for label_ip in ${WG_PEERS}; do
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

WG_HUB=$(python3 - "${PROJ_ROOT}/hosts_map.yml" <<'PYEOF'
import yaml, sys
d = yaml.safe_load(open(sys.argv[1]))
for h in d.get('groups', {}).get('kvm', {}).values():
    if h.get('wg_role') == 'hub':
        print(h.get('wg_ip', ''))
        break
PYEOF
)

SACONSOLE_REACHABLE=false
if [[ -n "${WG_HUB}" ]] && ping -c1 -W2 "${WG_HUB}" &>/dev/null; then
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

# ── 11. ERPNext sites ─────────────────────────────────────────────────────────
hdr "11. ERPNext sites"

ERP_SITES=$(python3 - "${PROJ_ROOT}/hosts_map.yml" <<'PYEOF'
import yaml, sys
d = yaml.safe_load(open(sys.argv[1]))
for name, h in d.get('groups', {}).get('kvm', {}).items():
    role = h.get('vm_role', '')
    if not role:
        continue
    zone = role.split(':')[0] if ':' in role else 'development'
    domain = 'logichem.solutions' if zone == 'production' else 'iridium.blue'
    print(f'{name}:https://{name}.{domain}')
PYEOF
)

if [[ -z "${ERP_SITES}" ]]; then
    warn "No ERPNext hosts found in hosts_map.yml (no hosts with vm_role set)"
else
    for label_url in ${ERP_SITES}; do
        label="${label_url%%:*}"
        url="${label_url#*:}"
        HTTP_CODE=$(curl -s --max-time 8 "${url}" -o /dev/null -w "%{http_code}" 2>/dev/null; true)
        [[ -z "${HTTP_CODE}" ]] && HTTP_CODE="000"
        if [[ "${HTTP_CODE}" =~ ^(200|301|302)$ ]]; then
            ok "ERPNext ${label} (${url}) — HTTP ${HTTP_CODE}"
        elif [[ "${HTTP_CODE}" == "000" ]]; then
            warn "ERPNext ${label} (${url}) — unreachable"
            fix "Check VM is running and nginx/bench are up on ${label}"
        else
            warn "ERPNext ${label} (${url}) — HTTP ${HTTP_CODE}"
        fi
    done
fi

# ── 12. MCP endpoints ─────────────────────────────────────────────────────────
hdr "12. MCP endpoints"

# Derived from settings.json — all SSE-type MCP servers are live infrastructure
SSE_ENDPOINTS=$(python3 - "${HOME}/.claude/settings.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
for name, cfg in d.get('mcpServers', {}).items():
    if cfg.get('type') == 'sse':
        print(f'{name}:{cfg["url"]}')
PYEOF
)

for label_url in ${SSE_ENDPOINTS}; do
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
        fix "Check that the container is running and network path is open"
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

if gh auth status &>/dev/null; then
    ok "github token — authenticated (gh auth status OK)"
else
    fail "github token — not authenticated"
    fix "Run: gh auth login"
fi

# ── 14. Cloudflare MCP ────────────────────────────────────────────────────────
hdr "14. Cloudflare MCP"

if command -v npx &>/dev/null; then
    ok "npx available ($(npx --version 2>/dev/null))"
else
    fail "npx not found — Cloudflare MCP requires Node.js/npm"
    fix "Install Node.js: https://nodejs.org"
fi

CF_REFRESH="${HOME}/.local/bin/cf-mcp-refresh"
if [[ -x "${CF_REFRESH}" ]]; then
    ok "cf-mcp-refresh present at ${CF_REFRESH}"
else
    fail "cf-mcp-refresh not found at ${CF_REFRESH}"
    fix "GH #50: copy tools/cf-mcp-refresh to ~/.local/bin/ and chmod +x"
fi

if grep -q 'cloudflare' "${HOME}/.claude/settings.json" 2>/dev/null; then
    ok "cloudflare MCP entry present in ~/.claude/settings.json"
else
    fail "cloudflare MCP not configured in ~/.claude/settings.json"
    fix "Add cloudflare entry (type: stdio) pointing to mcp-remote binary"
fi

# Verify settings.json uses absolute path to mcp-remote, not npx
CF_CMD=$(python3 -c "
import json, sys
try:
    d = json.load(open('${HOME}/.claude/settings.json'))
    print(d.get('mcpServers', {}).get('cloudflare', {}).get('command', ''))
except Exception:
    pass
" 2>/dev/null)
if [[ "${CF_CMD}" == "npx" ]]; then
    warn "cloudflare MCP uses 'npx' — may pause for interactive install confirmation"
    fix "Set command to absolute mcp-remote path in ~/.claude/settings.json (see reference_mcp_remote_tokens.md)"
elif [[ -n "${CF_CMD}" && "${CF_CMD}" != "npx" ]]; then
    if [[ -x "${CF_CMD}" ]]; then
        ok "cloudflare MCP command is absolute path and executable: ${CF_CMD}"
    else
        fail "cloudflare MCP command not executable: ${CF_CMD}"
        fix "Check mcp-remote is installed: npm install -g mcp-remote"
    fi
fi

# Functional test: run cf-mcp-refresh and confirm it obtains a fresh token
if [[ -x "${CF_REFRESH}" ]]; then
    CF_REFRESH_OUT=$("${CF_REFRESH}" 2>&1)
    CF_REFRESH_RC=$?
    if [[ $CF_REFRESH_RC -eq 0 ]] && echo "${CF_REFRESH_OUT}" | grep -q "✅"; then
        ok "cf-mcp-refresh — token refreshed successfully"
    elif echo "${CF_REFRESH_OUT}" | grep -qi "manual re-auth"; then
        fail "cloudflare MCP — no token cache or refresh_token missing; manual re-auth required"
        fix "Run in terminal: npx mcp-remote https://mcp.cloudflare.com/mcp  (complete browser auth, then Ctrl+C)"
    else
        warn "cf-mcp-refresh — unexpected output: ${CF_REFRESH_OUT}"
        fix "Check network access to https://mcp.cloudflare.com/token"
    fi
fi

# ── 15. Telegram notification channel ────────────────────────────────────────
hdr "15. Telegram notification channel"

TG_TOKEN=$(sops -d "${ANSIBLE_DIR}/group_vars/all.sops.yml" 2>/dev/null \
    | grep '^telegram_bot_token:' | awk '{print $2}')

if [[ -z "${TG_TOKEN}" ]]; then
    fail "Telegram bot token not found — SOPS decryption failed or key missing"
    fix "Verify: sops -d ansible/group_vars/all.sops.yml | grep telegram"
else
    TG_RESPONSE=$(curl -sf --max-time 5 \
        "https://api.telegram.org/bot${TG_TOKEN}/getMe" 2>/dev/null || true)
    if echo "${TG_RESPONSE}" | python3 -c \
        "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('ok') else 1)" 2>/dev/null; then
        BOT_NAME=$(echo "${TG_RESPONSE}" | python3 -c \
            "import json,sys; d=json.load(sys.stdin); print(d['result']['username'])" 2>/dev/null)
        ok "Telegram bot @${BOT_NAME} — token valid, API reachable"
    else
        fail "Telegram bot API call failed — token invalid or api.telegram.org unreachable"
        fix "Check token in ansible/group_vars/all.sops.yml and network access"
    fi
fi

# ── 16. Cytoscape prototype API ───────────────────────────────────────────────
hdr "16. Cytoscape prototype API"

HTTP_CODE=$(curl -s --max-time 3 http://localhost:8088/api/hosts \
    -o /dev/null -w "%{http_code}" 2>/dev/null; true)
[[ -z "${HTTP_CODE}" ]] && HTTP_CODE="000"
if [[ "${HTTP_CODE}" == "200" ]]; then
    ok "Cytoscape API (http://localhost:8088) — responding"
elif [[ "${HTTP_CODE}" == "000" ]]; then
    warn "Cytoscape API not running — start when doing control plane work"
    fix "uvicorn tools.api:app --port 8088 --reload  (from project root)"
else
    warn "Cytoscape API — HTTP ${HTTP_CODE} (unexpected)"
fi

# ── 17. Claude in Chrome — ERPNext site view ──────────────────────────────────
hdr "17. Claude in Chrome"

# Build expected ERPNext hostnames from hosts_map.yml
ERP_HOSTS=$(python3 - "${PROJ_ROOT}/hosts_map.yml" <<'PYEOF'
import yaml, sys
d = yaml.safe_load(open(sys.argv[1]))
for name, h in d.get('groups', {}).get('kvm', {}).items():
    role = h.get('vm_role', '')
    if not role:
        continue
    zone = role.split(':')[0] if ':' in role else 'development'
    domain = 'logichem.solutions' if zone == 'production' else 'iridium.blue'
    print(f'{name}.{domain}')
PYEOF
)

# Check Chrome is running (extension connects to Claude Code — no debug port needed)
if pgrep -x "google-chrome" &>/dev/null || pgrep -x "chromium-browser" &>/dev/null \
    || pgrep -x "chromium" &>/dev/null; then
    CHROME_RUNNING=true
    ok "Chrome process is running"
else
    CHROME_RUNNING=false
    warn "Chrome is not running — Claude in Chrome unavailable"
    fix "Open Chrome, install the Claude extension, then launch via ./Cld.sh"
fi

if [[ "${CHROME_RUNNING}" == true ]]; then
    if [[ -n "${ERP_HOSTS}" ]]; then
        ERP_LIST=$(echo "${ERP_HOSTS}" | tr '\n' ' ')
        warn "Verify manually: Chrome should have a tab open on one of: ${ERP_LIST}"
        fix "After session starts, confirm via /mcp that claude-in-chrome tools are available"
    else
        warn "No ERPNext hosts in hosts_map.yml — nothing to view in Chrome"
    fi
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
