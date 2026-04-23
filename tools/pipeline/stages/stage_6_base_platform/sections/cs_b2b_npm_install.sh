#!/usr/bin/env bash
set -euo pipefail
# Section B2b: npm install for ce_sri_svc. Restore-mode only.
# Needs env: BENCH_DIR, ERP_USER
echo "=== B2b: npm install for ce_sri_svc ==="
_CESRI_SVC="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
if [ -f "$_CESRI_SVC/package.json" ]; then
    sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && npm install 2>&1"
    echo "  [OK] npm install completed for ce_sri_svc"
else
    echo "  [SKIP] no package.json in ce_sri_svc"
fi
