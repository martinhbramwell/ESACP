#!/usr/bin/env bash
set -euo pipefail
# Section A2d (BaRe): clone/pull BaRe (HTTPS, no deploy key). Both modes.
# Needs env: BENCH_DIR, ERP_USER
echo "=== A2d (BaRe): clone/pull BaRe ==="
if [ ! -d "$BENCH_DIR/BaRe/.git" ]; then
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && git clone https://github.com/martinhbramwell/BaRe.git BaRe"
    echo "  [OK] BaRe cloned"
else
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR/BaRe && git checkout main && git pull"
    echo "  [OK] BaRe pulled"
fi
