#!/usr/bin/env bash
# Stage 9 (generic mode): Service activation — stop.py + bash_aliases only.
# Social Login is skipped (no ce_sri / production OAuth config).
#
# Usage: sudo bash generic_activation.sh <bench_dir> <site_url> <erp_user>
set -euo pipefail

BENCH_DIR="${1:?Usage: generic_activation.sh <bench_dir> <site_url> <erp_user>}"
SITE_URL="${2:?Usage: generic_activation.sh <bench_dir> <site_url> <erp_user>}"
ERP_USER="${3:?Usage: generic_activation.sh <bench_dir> <site_url> <erp_user>}"

echo "=== [SKIP] Social Login — generic mode ==="

# ── Section L0: deploy stop.py ──────────────────────────────────────
echo "=== L0: deploy stop.py ==="
if [ -f /tmp/rendered/stop.py ]; then
    cp /tmp/rendered/stop.py "${BENCH_DIR}/stop.py"
    chown "${ERP_USER}:${ERP_USER}" "${BENCH_DIR}/stop.py"
    chmod 755 "${BENCH_DIR}/stop.py"
    echo "  [OK] stop.py deployed to ${BENCH_DIR}"
else
    echo "  [SKIP] stop.py not found in /tmp/rendered/"
fi

# ── Section L: render bash_aliases ──────────────────────────────────
echo "=== L: render bash_aliases ==="
if [ -f /tmp/renderers/render_bash_aliases.py ]; then
    DB_NAME=$(python3 -c "import json; print(json.load(open('${BENCH_DIR}/sites/${SITE_URL}/site_config.json'))['db_name'])" 2>/dev/null || echo "unknown_db")
    python3 /tmp/renderers/render_bash_aliases.py \
        --template /tmp/templates/bash_aliases.j2 \
        --params /tmp/rendered/params.json \
        --output "/home/${ERP_USER}/.bash_aliases" \
        --extra "db_name=${DB_NAME}"
    chown "${ERP_USER}:${ERP_USER}" "/home/${ERP_USER}/.bash_aliases"
    echo "  [OK] .bash_aliases rendered for ${ERP_USER}"
else
    echo "  [SKIP] render_bash_aliases.py not found"
fi

echo "=== Generic service activation complete ==="
