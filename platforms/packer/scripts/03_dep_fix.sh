#!/usr/bin/env bash
# 03_dep_fix.sh — Frappe v13 Python dependency fix
#
# Runs INSIDE the build VM as the bench user (via: sudo -Hu ${erp_user} env ERP_USER=... bash {{ .Path }})
#
# Background (see feedback_frappe_v13_deps.md):
#   bench init uses 'uv pip install --upgrade' which pulls package versions
#   incompatible with Frappe v13's pins:
#     - setuptools >= 71 removes pkg_resources from the default install
#     - urllib3 2.x breaks botocore 1.20.x (a Frappe v13 dependency)
#
# Fix: pin setuptools to 70.3.0, then reinstall requirements from Frappe's own
# requirements.txt to restore the pinned versions.

set -euo pipefail

# ERP_USER is passed by Packer execute_command — not hardcoded here.
ERP_USER="${ERP_USER:?ERP_USER env var not set — pass via Packer execute_command}"

# This fix is Frappe v13-specific (setuptools 70.3.0 pin restores pkg_resources;
# urllib3/botocore pins). On v15+ those pins are wrong and would downgrade a
# healthy environment, so this phase is a deliberate no-op off the v13 line.
# FRAPPE_BRANCH is passed by Packer execute_command (dual-template; ESACP #631).
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-13}"
if [[ "${FRAPPE_BRANCH}" != "version-13" ]]; then
    echo "[03_dep_fix $(date '+%H:%M:%S')] frappe ${FRAPPE_BRANCH} is not the v13 line — skipping v13 dependency fix."
    exit 0
fi

cd "$HOME"
BENCH_DIR="${HOME}/frappe-bench"
BENCH_PIP="${BENCH_DIR}/env/bin/pip"

log() { echo "[03_dep_fix $(date '+%H:%M:%S')] $*"; }

[[ "$(whoami)" == "${ERP_USER}" ]] || { echo "ERROR: must run as ${ERP_USER} (got: $(whoami))"; exit 1; }
[[ -d "${BENCH_DIR}/env" ]]  || { echo "ERROR: bench env not found at ${BENCH_DIR}/env"; exit 1; }

log "Fix 1: pin setuptools to 70.3.0 (restores pkg_resources) ..."
"${BENCH_PIP}" install -q 'setuptools==70.3.0'

log "Fix 2: reinstall pinned requirements from frappe + erpnext requirements.txt ..."
"${BENCH_PIP}" install -q \
    -r "${BENCH_DIR}/apps/frappe/requirements.txt" \
    -r "${BENCH_DIR}/apps/erpnext/requirements.txt" \
    2>&1 | grep -E '(ERROR|Successfully installed|Uninstalling|Requirement already)' || true

log "✓  Frappe v13 dependency fix applied"
