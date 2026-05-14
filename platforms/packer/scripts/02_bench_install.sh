#!/usr/bin/env bash
# 02_bench_install.sh — bench init + frappe + erpnext app install
#
# Runs INSIDE the build VM as the bench user (via: sudo -Hu ${erp_user} env ERP_USER=... bash {{ .Path }})
# Environment vars set by Packer: FRAPPE_BRANCH, ERPNEXT_BRANCH, ERP_USER
#
# Result: /home/${ERP_USER}/frappe-bench with frappe + erpnext installed.
# NO bench new-site. NO bespoke apps. NO production data.
# This is the "undifferentiated" state — everything site-specific is added at deploy time.

set -euo pipefail

# ERP_USER is passed by Packer execute_command — not hardcoded here.
ERP_USER="${ERP_USER:?ERP_USER env var not set — pass via Packer execute_command}"

# Ensure we are in the bench user's home — bench CLI startup checks ./apps in cwd.
# sudo -Hu sets HOME correctly but cwd may still be the SSH user's dir.
cd "$HOME"

FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-13}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-version-13}"
BENCH_DIR="${HOME}/frappe-bench"

log() { echo "[02_bench $(date '+%H:%M:%S')] $*"; }

# ── Yanked-transitive-dep overrides ───────────────────────────────────────────
# Frappe pins transitive deps by range; some later get yanked from PyPI. uv
# accepts yanked versions only when pinned exactly (PEP 592). Tag-gated because
# the override would downgrade transitive deps on tags that don't need it. (#392)

case "${FRAPPE_BRANCH}" in
    v13.41.3)
        log "applying uv override for ${FRAPPE_BRANCH}: braintree==4.8.0 (yanked, only candidate)"
        mkdir -p "${HOME}/.config/uv"
        cat > "${HOME}/.config/uv/uv.toml" <<'UV_TOML'
override-dependencies = ["braintree==4.8.0"]
UV_TOML
        ;;
esac

# ── Sanity checks ──────────────────────────────────────────────────────────────

[[ "$(whoami)" == "${ERP_USER}" ]] || { echo "ERROR: must run as ${ERP_USER} (got: $(whoami))"; exit 1; }

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
