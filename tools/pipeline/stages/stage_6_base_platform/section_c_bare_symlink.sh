#!/usr/bin/env bash
set -euo pipefail

# Section C: BaRe/envars.sh -> /opt/ce_sri/envars.sh symlink (gated, runs after BaRe clone)
# Usage: section_c_bare_symlink.sh BENCH_DIR ERP_USER PROVISION_MODE

BENCH_DIR="$1"
ERP_USER="$2"
PROVISION_MODE="${3:-restored}"

echo "=== C: BaRe/envars.sh symlink ==="
if [ "$PROVISION_MODE" = "generic" ]; then
    echo "  [SKIP] generic mode — BaRe is self-standing, no envars.sh symlink"
    exit 0
fi

if [ -d "$BENCH_DIR/BaRe" ]; then
    sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
    echo "  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh"
else
    echo "  [WARN] $BENCH_DIR/BaRe not found"
fi
