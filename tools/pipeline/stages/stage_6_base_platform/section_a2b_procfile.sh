#!/usr/bin/env bash
set -euo pipefail

# Section A2b: deploy Procfile with ce_sri_svc entry (gated)
# Usage: section_a2b_procfile.sh BENCH_DIR ERP_USER PROVISION_MODE

BENCH_DIR="$1"
ERP_USER="$2"
PROVISION_MODE="${3:-restored}"

echo "=== A2b: deploy Procfile ==="
if [ "$PROVISION_MODE" = "generic" ]; then
    echo "  [SKIP] generic mode — bench-default Procfile retained (no ce_sri_svc)"
    exit 0
fi

PROCFILE="$BENCH_DIR/Procfile"
if ! grep -q 'ce_sri_svc' "$PROCFILE" 2>/dev/null; then
    cp /tmp/rendered/Procfile "$PROCFILE"
    chown "$ERP_USER:$ERP_USER" "$PROCFILE"
    echo "  [OK] Procfile deployed"
else
    echo "  [OK] Procfile already contains ce_sri_svc — skipping"
fi
