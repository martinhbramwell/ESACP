#!/usr/bin/env bash
set -euo pipefail

# Section A2d (BaRe): clone BaRe (always, HTTPS-public)
# Usage: section_a2d_clone_bare.sh BENCH_DIR ERP_USER

BENCH_DIR="$1"
ERP_USER="$2"

echo "=== A2d (BaRe): clone BaRe ==="
if [ ! -d "$BENCH_DIR/BaRe/.git" ]; then
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && git clone https://github.com/martinhbramwell/BaRe.git BaRe"
    echo "  [OK] BaRe cloned"
else
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR/BaRe && git checkout main && git pull"
    echo "  [OK] BaRe pulled"
fi
