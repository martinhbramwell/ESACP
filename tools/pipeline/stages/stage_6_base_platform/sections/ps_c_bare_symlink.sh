#!/usr/bin/env bash
set -euo pipefail
# Section C: BaRe/envars.sh -> mode-specific envars target.
# Needs env: BENCH_DIR, ERP_USER, ENVARS_PATH
echo "=== C: BaRe/envars.sh symlink ==="
if [ -d "$BENCH_DIR/BaRe" ]; then
    sudo -u "$ERP_USER" ln -sf "$ENVARS_PATH" "$BENCH_DIR/BaRe/envars.sh"
    echo "  [OK] BaRe/envars.sh -> $ENVARS_PATH"
else
    echo "  [SKIP] $BENCH_DIR/BaRe not yet cloned — will link after clone_and_services.sh"
fi
