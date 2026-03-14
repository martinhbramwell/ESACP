#!/usr/bin/env bash
# full_provision.sh — One-command VBox lab: revert → WireGuard → handoff → provision.
#
# Sets NO_TELEGRAM=1 so each individual script suppresses its own alert.
# Sends a single Telegram summary on completion (success or failure).
#
# Usage (from project root):
#   bash platforms/vbox/full_provision.sh

set -euo pipefail

export NO_TELEGRAM=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

BOOTSTRAP_USER="you"
BOOTSTRAP_PASSWORD="wawa"
BRANCH=$(git rev-parse --abbrev-ref HEAD)

hdr() { echo ""; echo "════════════════════════════════════════"; echo "  $1"; echo "════════════════════════════════════════"; }

# shellcheck source=utils.sh
source "${SCRIPT_DIR}/utils.sh"

_PHASE="init"

_tg_on_exit() {
    local rc=$?
    if [[ $rc -eq 0 ]]; then
        tg_notify "✅ ESACP full provision complete
Branch: ${BRANCH}
All 4 phases succeeded."
    else
        tg_notify "❌ ESACP full provision FAILED
Branch: ${BRANCH}
Phase: ${_PHASE}
Exit: ${rc}"
    fi
}
trap '_tg_on_exit' EXIT

# ── Phase 1: Revert to Fresh Install ─────────────────────────────────────────

_PHASE="revert_to_fresh"
hdr "Phase 1 — revert_to_fresh"
bash platforms/vbox/revert_to_fresh.sh

# ── Phase 2: Install WireGuard ───────────────────────────────────────────────

_PHASE="install_wireguard"
hdr "Phase 2 — install_wireguard"
bash platforms/vbox/install_wireguard.sh

# ── Phase 3: Handoff to saconsole ────────────────────────────────────────────

_PHASE="handoff_console"
hdr "Phase 3 — handoff_console"
bash platforms/vbox/handoff_console.sh

CONSOLE_IP=$(</tmp/.esacp_console_ip)

# ── Phase 4: Full Ansible provision (runs on saconsole) ──────────────────────
#
# sshpass used because key auth is not yet configured at this point.
# ServerAliveInterval keeps the connection alive during long Ansible runs.
# NO_TELEGRAM=1 is set inline — env vars do not cross SSH automatically.

_PHASE="provision_targets"
hdr "Phase 4 — provision_targets (on saconsole ${CONSOLE_IP})"
sshpass -p "${BOOTSTRAP_PASSWORD}" ssh \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=20 \
    "${BOOTSTRAP_USER}@${CONSOLE_IP}" \
    'NO_TELEGRAM=1 bash /opt/esacp/platforms/vbox/provision_targets.sh'

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅  Full provision complete."
echo ""
echo "  Grafana:    http://${CONSOLE_IP}:3000"
echo "  Prometheus: http://${CONSOLE_IP}:9090"
echo "  Cytoscape:  http://${CONSOLE_IP}:8090"
echo "════════════════════════════════════════════════════════════════"
