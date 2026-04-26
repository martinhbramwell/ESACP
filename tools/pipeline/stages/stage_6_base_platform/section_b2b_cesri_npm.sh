#!/usr/bin/env bash
set -euo pipefail

# Section B2b: npm install for ce_sri_svc (gated)
# Usage: section_b2b_cesri_npm.sh BENCH_DIR ERP_USER PROVISION_MODE

BENCH_DIR="$1"
ERP_USER="$2"
PROVISION_MODE="${3:-restored}"

echo "=== B2b: npm install for ce_sri_svc ==="
if [ "$PROVISION_MODE" = "generic" ]; then
    echo "  [SKIP] generic mode — no ce_sri_svc app to npm-install"
    exit 0
fi

_CESRI_SVC="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
if [ -f "$_CESRI_SVC/package.json" ]; then
    sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && npm install 2>&1"
    echo "  [OK] npm install completed for ce_sri_svc"
else
    echo "  [SKIP] no package.json in ce_sri_svc"
fi
