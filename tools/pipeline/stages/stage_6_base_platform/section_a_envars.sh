#!/usr/bin/env bash
set -euo pipefail

# Section A: deploy /opt/ce_sri/envars.sh (gated on PROVISION_MODE)
# Usage: section_a_envars.sh PROVISION_MODE

PROVISION_MODE="${1:-restored}"

echo "=== A: deploy pre-rendered envars.sh ==="
if [ "$PROVISION_MODE" = "generic" ]; then
    echo "  [SKIP] generic mode — BaRe is self-standing, no /opt/ce_sri/envars.sh"
    exit 0
fi

sudo mkdir -p /opt/ce_sri
sudo cp /tmp/rendered/envars.sh /opt/ce_sri/envars.sh
sudo chmod 644 /opt/ce_sri/envars.sh
echo "  [OK] /opt/ce_sri/envars.sh"
