#!/usr/bin/env bash
set -euo pipefail

# Section A2: symlink bench dir (always)
# Usage: section_a2_bench_symlink.sh BENCH_DIR BENCH_DIR_ORIG ERP_USER

BENCH_DIR="$1"
BENCH_DIR_ORIG="$2"
ERP_USER="$3"

echo "=== A2: symlink bench dir ==="
if sudo test -d "$BENCH_DIR_ORIG" && ! sudo test -L "$BENCH_DIR"; then
    sudo -u "$ERP_USER" ln -sf "$BENCH_DIR_ORIG" "$BENCH_DIR"
    echo "  [OK] symlinked $BENCH_DIR_ORIG -> $BENCH_DIR"
elif sudo test -L "$BENCH_DIR"; then
    echo "  [OK] $BENCH_DIR symlink already exists — skipping"
else
    echo "  [ERROR] Neither $BENCH_DIR_ORIG nor $BENCH_DIR found"
    exit 1
fi
