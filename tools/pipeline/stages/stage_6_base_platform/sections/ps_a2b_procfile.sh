#!/usr/bin/env bash
set -euo pipefail
# Section A2b: deploy Procfile with ce_sri_svc entry. Restore-mode only.
# Needs env: BENCH_DIR, ERP_USER
echo "=== A2b: deploy Procfile ==="
PROCFILE="$BENCH_DIR/Procfile"
if ! grep -q 'ce_sri_svc' "$PROCFILE" 2>/dev/null; then
    cp /tmp/rendered/Procfile "$PROCFILE"
    chown "$ERP_USER:$ERP_USER" "$PROCFILE"
    echo "  [OK] Procfile deployed"
else
    echo "  [OK] Procfile already contains ce_sri_svc — skipping"
fi
