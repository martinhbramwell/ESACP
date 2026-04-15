#!/usr/bin/env bash
# rebuild_lab.sh — Full KVM lab rebuild: destroy → hub → targets.
#
# Chains three phases:
#   1. destroy_vms.sh         — tear down all 3 VMs on toshiba, clear artifacts
#   2. bootstrap_hub.sh — 9-phase hub bootstrap (from this controller)
#   3. bootstrap_targets.sh   — 9-phase targets bootstrap (from hub via SSH)
#
# bootstrap_targets.sh runs FROM the hub because:
#   - Ansible uses the hub's ~/.ssh/id_ed25519 to reach targets
#     (the only SSH key injected into targets via cloud-init)
#   - the hub SSHes to toshiba as hasan@toshiba using that same key
#     (installed on toshiba in Phase 9 of bootstrap_hub.sh)
#
# Sends a Telegram notification on success or failure.
#
# Usage (from project root):
#   bash platforms/kvm/rebuild_lab.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Configuration (from hosts_map.yml + env overrides) ────────────────────────
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

cd "${PROJ_ROOT}"

BRANCH=$(git rev-parse --abbrev-ref HEAD)

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

# ── Phase 2: Bootstrap hub (from this controller) ───────────────────────

_PHASE="bootstrap_hub"
hdr "Phase 2 — Bootstrap hub"
bash "${SCRIPT_DIR}/bootstrap_hub.sh"

# ── Phase 3: Bootstrap targets (from hub) ────────────────────────────────
#
# ServerAliveInterval keeps the connection live during the ~60-minute provision.

_PHASE="bootstrap_targets"
hdr "Phase 3 — Bootstrap targets (from hub)"
ssh \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=ERROR \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=20 \
    -J "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" \
    -i "${SSH_KEY}" \
    "${HUB_USER}@${HUB_VIRBR0_IP}" \
    'bash /opt/esacp/platforms/kvm/bootstrap_targets.sh'

# ── Done ──────────────────────────────────────────────────────────────────────

hdr "Done"
echo "  All KVM VMs (${ESACP_KVM_VMS}) are provisioned."
echo ""
echo "  Grafana:       http://${HUB_WG_IP}:3000"
echo "  Prometheus:    http://${HUB_WG_IP}:9090"
echo "  mcp-grafana:   http://${HUB_WG_IP}:8000/sse"
echo ""
echo "  Next: bash platforms/kvm/sync_check.sh"
echo ""
