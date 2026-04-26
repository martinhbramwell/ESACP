#!/usr/bin/env bash
set -euo pipefail

# Section B: fix ownership of BKP directory (always, idempotent)
# Usage: section_b_bkp_owner.sh BENCH_DIR ERP_USER

BENCH_DIR="$1"
ERP_USER="$2"

echo "=== B: fix ownership of BKP ==="
if [ -d "$BENCH_DIR/BKP" ]; then
    sudo chown -R "$ERP_USER:$ERP_USER" "$BENCH_DIR/BKP"
    echo "  [OK] BKP ownership -> $ERP_USER"
else
    echo "  [SKIP] $BENCH_DIR/BKP not found"
fi
