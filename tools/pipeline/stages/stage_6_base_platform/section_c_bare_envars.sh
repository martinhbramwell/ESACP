#!/usr/bin/env bash
set -euo pipefail

# Section C: deploy BaRe/envars.sh (mode-aware).
#   ce_sri (existing): symlink BaRe/envars.sh -> /opt/ce_sri/envars.sh
#   generic:           copy /tmp/rendered/envars.sh to BaRe/envars.sh as a real file
# Stage 4 renders /tmp/rendered/envars.sh in both modes from hosts_map.yml +
# group_vars + secrets, so the same site-identity content is available either way.
# Usage: section_c_bare_envars.sh BENCH_DIR ERP_USER PROVISION_MODE

BENCH_DIR="$1"
ERP_USER="$2"
PROVISION_MODE="${3:-restored}"

echo "=== C: BaRe/envars.sh deployment (mode=${PROVISION_MODE}) ==="

if [ ! -d "$BENCH_DIR/BaRe" ]; then
    echo "  [WARN] $BENCH_DIR/BaRe not found"
    exit 0
fi

if [ "$PROVISION_MODE" = "generic" ]; then
    if [ ! -f /tmp/rendered/envars.sh ]; then
        echo "  [FAIL] /tmp/rendered/envars.sh missing — Stage 4 should render it"
        exit 1
    fi
    sudo cp /tmp/rendered/envars.sh "$BENCH_DIR/BaRe/envars.sh"
    sudo chown "$ERP_USER:$ERP_USER" "$BENCH_DIR/BaRe/envars.sh"
    sudo chmod 644 "$BENCH_DIR/BaRe/envars.sh"
    echo "  [OK] $BENCH_DIR/BaRe/envars.sh (real file, generic-mode site identity)"
else
    sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
    echo "  [OK] $BENCH_DIR/BaRe/envars.sh -> /opt/ce_sri/envars.sh"
fi
