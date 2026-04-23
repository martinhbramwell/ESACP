#!/usr/bin/env bash
set -euo pipefail
# Section B: fix ownership of BKP dir.
# Needs env: BENCH_DIR, ERP_USER
echo "=== B: fix ownership of BKP ==="
if [ -d "$BENCH_DIR/BKP" ]; then
    sudo chown -R "$ERP_USER:$ERP_USER" "$BENCH_DIR/BKP"
    echo "  [OK] BKP ownership -> $ERP_USER"
else
    echo "  [SKIP] $BENCH_DIR/BKP not found"
fi
