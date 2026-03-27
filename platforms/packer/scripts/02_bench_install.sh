#!/usr/bin/env bash
# 02_bench_install.sh — bench init + frappe + erpnext app install
#
# Runs INSIDE the build VM as user 'adm' (via: sudo -u adm bash {{ .Path }})
# Environment vars set by Packer: FRAPPE_BRANCH, ERPNEXT_BRANCH
#
# Result: /home/adm/frappe-bench with frappe + erpnext installed.
# NO bench new-site. NO bespoke apps. NO production data.
# This is the "undifferentiated" state — everything site-specific is added at deploy time.

set -euo pipefail

# Ensure we are in adm's home — bench CLI startup checks ./apps in cwd.
# sudo -Hu sets HOME=/home/adm but cwd may still be the SSH user's dir.
cd /home/adm

FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-13}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-version-13}"
BENCH_DIR="${HOME}/frappe-bench"

log() { echo "[02_bench $(date '+%H:%M:%S')] $*"; }

# ── Sanity checks ──────────────────────────────────────────────────────────────

[[ "$(whoami)" == "adm" ]] || { echo "ERROR: must run as adm"; exit 1; }

command -v bench &>/dev/null   || { echo "ERROR: bench CLI not found (phase 1 incomplete?)"; exit 1; }
command -v node  &>/dev/null   || { echo "ERROR: node not found"; exit 1; }
command -v mysql &>/dev/null   || { echo "ERROR: mysql not found"; exit 1; }

# ── bench init ────────────────────────────────────────────────────────────────

log "bench init ${BENCH_DIR} (frappe ${FRAPPE_BRANCH}) ..."
if [[ -d "${BENCH_DIR}" ]]; then
    log "  ${BENCH_DIR} already exists — skipping bench init."
else
    bench init \
        --frappe-branch "${FRAPPE_BRANCH}" \
        --python python3 \
        "${BENCH_DIR}"
fi

cd "${BENCH_DIR}"

# ── get-app erpnext ───────────────────────────────────────────────────────────

log "bench get-app erpnext (${ERPNEXT_BRANCH}) ..."
if [[ -d "${BENCH_DIR}/apps/erpnext" ]]; then
    log "  erpnext already present — skipping get-app."
else
    bench get-app erpnext --branch "${ERPNEXT_BRANCH}"
fi

# ── setup requirements ────────────────────────────────────────────────────────

log "bench setup requirements ..."
bench setup requirements

log "✓  bench install complete — frappe + erpnext apps present, no site created"
