#!/usr/bin/env bash
set -euo pipefail
# Section A: deploy pre-rendered envars.sh at mode-specific path.
# Needs env: MODE, ENVARS_DIR, ENVARS_PATH
echo "=== A: deploy envars.sh ($MODE -> $ENVARS_PATH) ==="
sudo mkdir -p "$ENVARS_DIR"
sudo cp /tmp/rendered/envars.sh "$ENVARS_PATH"
sudo chmod 644 "$ENVARS_PATH"
echo "  [OK] $ENVARS_PATH"
