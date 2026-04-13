#!/usr/bin/env bash
# Stage 9: Service Activation — Social Login + stop.py + bash_aliases.
#
# Usage: sudo bash service_activation.sh <bench_dir> <site_url> <erp_user>
#
# Expects (from earlier stages):
#   /tmp/socials_google.json  (Stage 3 cesri_secrets — placed into site dir here)
#   $BENCH_DIR/sites/$SITE_URL/private/files/apikey.sh  (Stage 8 H4a)
#   /tmp/rendered/stop.py  (Stage 4 config_bundle)
#   /tmp/renderers/render_bash_aliases.py + /tmp/templates/bash_aliases.j2
#   /tmp/rendered/params.json
set -euo pipefail

BENCH_DIR="${1:?Usage: service_activation.sh <bench_dir> <site_url> <erp_user>}"
SITE_URL="${2:?Usage: service_activation.sh <bench_dir> <site_url> <erp_user>}"
ERP_USER="${3:?Usage: service_activation.sh <bench_dir> <site_url> <erp_user>}"

# ── Section H4a-sl: restore Social Login config ─────────────────────
echo "=== H4a-sl: restore Social Login config ==="
SOCIAL_CONF="${BENCH_DIR}/sites/${SITE_URL}/socials_google.json"
if [ -f /tmp/socials_google.json ]; then
    sudo -u "${ERP_USER}" cp /tmp/socials_google.json "${SOCIAL_CONF}"
    echo "  [OK] socials_google.json placed in site directory"
fi
APIKEY_SH="${BENCH_DIR}/sites/${SITE_URL}/private/files/apikey.sh"
if [ -f "${APIKEY_SH}" ] && [ -f "${SOCIAL_CONF}" ]; then
    source "${APIKEY_SH}"
    RESOURCE_URL="https://${SITE_URL}/api/resource"
    SWITCHES="--location --insecure --no-progress-meter --request"
    AUTH_HEADER="Authorization: token ${KEYS}"
    CONTENT_HEADER="Content-Type: application/json"
    SLK="Social%20Login%20Key"
    curl ${SWITCHES} DELETE --header "${AUTH_HEADER}" --header "${CONTENT_HEADER}" \
        "${RESOURCE_URL}/${SLK}/google" >/dev/null 2>&1 || true
    RSLT=$(curl ${SWITCHES} POST --header "${AUTH_HEADER}" --header "${CONTENT_HEADER}" \
        -d @"${SOCIAL_CONF}" "${RESOURCE_URL}/${SLK}")
    MSG=$(echo "${RSLT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['social_login_provider'])" 2>/dev/null || echo "unknown")
    echo "  [OK] Social Login restored (provider: ${MSG})"
elif [ ! -f "${APIKEY_SH}" ]; then
    echo "  [WARN] apikey.sh not found — cannot restore Social Login"
else
    echo "  [SKIP] socials_google.json not found — Social Login not configured"
fi

# ── Section L0: deploy stop.py ──────────────────────────────────────
echo "=== L0: deploy stop.py ==="
cp /tmp/rendered/stop.py "${BENCH_DIR}/stop.py"
chown "${ERP_USER}:${ERP_USER}" "${BENCH_DIR}/stop.py"
chmod 755 "${BENCH_DIR}/stop.py"
echo "  [OK] stop.py deployed to ${BENCH_DIR}"

# ── Section L: render bash_aliases ──────────────────────────────────
echo "=== L: render bash_aliases ==="
DB_NAME=$(python3 -c "import json; print(json.load(open('${BENCH_DIR}/sites/${SITE_URL}/site_config.json'))['db_name'])" 2>/dev/null || echo "unknown_db")
python3 /tmp/renderers/render_bash_aliases.py \
    --template /tmp/templates/bash_aliases.j2 \
    --params /tmp/rendered/params.json \
    --output "/home/${ERP_USER}/.bash_aliases" \
    --extra "db_name=${DB_NAME}"
chown "${ERP_USER}:${ERP_USER}" "/home/${ERP_USER}/.bash_aliases"
echo "  [OK] .bash_aliases rendered for ${ERP_USER}"
