#!/usr/bin/env bash
# rebuild_lab.sh — Full KVM lab rebuild: destroy → saconsole → targets.
#
# Chains three phases:
#   1. destroy_vms.sh         — tear down all 3 VMs on toshiba, clear artifacts
#   2. bootstrap_saconsole.sh — 9-phase saconsole bootstrap (from this controller)
#   3. bootstrap_targets.sh   — 9-phase targets bootstrap (from saconsole via SSH)
#
# bootstrap_targets.sh runs FROM saconsole because:
#   - Ansible uses saconsole's ~/.ssh/id_ed25519 to reach targets
#     (the only SSH key injected into targets via cloud-init)
#   - saconsole SSHes to toshiba as hasan@toshiba using that same key
#     (installed on toshiba in Phase 9 of bootstrap_saconsole.sh)
#
# Sends a Telegram notification on success or failure.
#
# Usage (from project root):
#   bash platforms/kvm/rebuild_lab.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

BRANCH=$(git rev-parse --abbrev-ref HEAD)
HYPERVISOR_ALIAS="toshy"
HYPERVISOR_USER="hasan"
SACONSOLE_IP="192.168.122.10"
SACONSOLE_USER="you"
SSH_KEY="${HOME}/.ssh/hasan_mighty"

# shellcheck source=utils.sh
source "${SCRIPT_DIR}/utils.sh"

hdr() {
    echo ""
    echo "════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════"
    echo ""
}

_PHASE="init"

_tg_on_exit() {
    local rc=$?
    if [[ $rc -eq 0 ]]; then
        tg_notify "✅ ESACP KVM rebuild complete
Branch: ${BRANCH}
All 3 phases succeeded."
    else
        tg_notify "❌ ESACP KVM rebuild FAILED
Branch: ${BRANCH}
Phase: ${_PHASE}
Exit: ${rc}"
    fi
}
trap '_tg_on_exit' EXIT

# ── Phase 1: Destroy ───────────────────────────────────────────────────────────

_PHASE="destroy_vms"
hdr "Phase 1 — Destroy VMs"
bash "${SCRIPT_DIR}/destroy_vms.sh"

# ── Phase 2: Bootstrap saconsole (from this controller) ───────────────────────

_PHASE="bootstrap_saconsole"
hdr "Phase 2 — Bootstrap saconsole"
bash "${SCRIPT_DIR}/bootstrap_saconsole.sh"

# ── Phase 3: Bootstrap targets (from saconsole) ────────────────────────────────
#
# ServerAliveInterval keeps the connection live during the ~60-minute provision.

_PHASE="bootstrap_targets"
hdr "Phase 3 — Bootstrap targets (from saconsole)"
ssh \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=ERROR \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=20 \
    -J "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
    -i "${SSH_KEY}" \
    "${SACONSOLE_USER}@${SACONSOLE_IP}" \
    'bash /opt/esacp/platforms/kvm/bootstrap_targets.sh'

# ── Done ──────────────────────────────────────────────────────────────────────

hdr "Done"
echo "  saconsole, target1, and target2 are provisioned."
echo ""
echo "  Grafana:       http://10.10.0.1:3000"
echo "  Prometheus:    http://10.10.0.1:9090"
echo "  mcp-grafana:   http://10.10.0.1:8000/sse"
echo "  MariaDB MCP:   http://10.10.0.3:9001/sse"
echo "                 http://10.10.0.4:9001/sse"
echo "  Nginx MCP:     http://10.10.0.3:9000/mcp"
echo "                 http://10.10.0.4:9000/mcp"
echo ""
echo "  Next: bash platforms/kvm/sync_check.sh"
echo ""
