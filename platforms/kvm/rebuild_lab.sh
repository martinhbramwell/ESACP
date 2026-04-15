#!/usr/bin/env bash
# rebuild_lab.sh — KVM hub rebuild: destroy all VMs → bootstrap hub.
#
# Chains two phases:
#   1. destroy_vms.sh     — tear down all VMs on toshiba, clear artifacts
#   2. bootstrap_hub.sh   — 9-phase hub bootstrap (from this controller)
#
# Target VMs (dev01, dev02, ...) are provisioned separately via:
#   - CLI:  python tools/esacp.py provision <hostname>
#   - API:  POST /api/provision/erpnext
#   - UI:   Cytoscape drag-to-provision
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
        tg_notify "✅ ESACP KVM hub rebuild complete
Branch: ${BRANCH}
Both phases succeeded."
    else
        tg_notify "❌ ESACP KVM hub rebuild FAILED
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

# ── Done ──────────────────────────────────────────────────────────────────────

hdr "Done"
echo "  Hub rebuilt successfully."
echo ""
echo "  Grafana:       http://${HUB_WG_IP}:3000"
echo "  Prometheus:    http://${HUB_WG_IP}:9090"
echo "  mcp-grafana:   http://${HUB_WG_IP}:8000/sse"
echo ""
echo "  Next: provision target VMs with:"
echo "    python tools/esacp.py provision <hostname>"
echo ""
echo "  Then verify: bash platforms/kvm/sync_check.sh"
echo ""
