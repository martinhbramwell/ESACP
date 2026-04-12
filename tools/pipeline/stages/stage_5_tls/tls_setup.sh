#!/usr/bin/env bash
# Stage 5: TLS — cert install + nginx vhost deploy + DH params + enable site.
#
# Usage: sudo bash tls_setup.sh <site_url> <domain>
#   site_url : e.g. dev03.iridium.blue
#   domain   : e.g. iridium.blue
#
# Expects:
#   /tmp/fullchain.pem + /tmp/privkey.pem   (from Stage 2 tls_cert)
#   /tmp/rendered/nginx_vhost.conf          (from Stage 4 config_bundle)
set -euo pipefail

SITE_URL="${1:?Usage: tls_setup.sh <site_url> <domain>}"
DOMAIN="${2:?Usage: tls_setup.sh <site_url> <domain>}"

CERT_DIR="/etc/nginx/certs/${DOMAIN}"
NGINX_CERT="${CERT_DIR}/fullchain.pem"
NGINX_KEY="${CERT_DIR}/privkey.pem"
NGINX_DHPARAM="/etc/nginx/dhparam.pem"

# ── Section I: Install TLS cert ──────────────────────────────────────
echo "=== I: install TLS cert ==="
mkdir -p "${CERT_DIR}"
if [ -f /tmp/fullchain.pem ]; then
    cp /tmp/fullchain.pem "${NGINX_CERT}"
    cp /tmp/privkey.pem   "${NGINX_KEY}"
    chmod 600 "${NGINX_KEY}"
    rm -f /tmp/fullchain.pem /tmp/privkey.pem /tmp/cert.pem
    echo "  [OK] certs installed to ${CERT_DIR}"
elif [ -f "${NGINX_CERT}" ]; then
    echo "  [OK] certs already in place at ${CERT_DIR} — skipping"
else
    echo "  [ERROR] no cert at /tmp/fullchain.pem and none at ${CERT_DIR}"
    exit 1
fi

# ── Section J: Deploy nginx vhost config ─────────────────────────────
echo "=== J: deploy nginx vhost config ==="
if [ ! -f /tmp/rendered/nginx_vhost.conf ]; then
    echo "  [ERROR] /tmp/rendered/nginx_vhost.conf not found"
    exit 1
fi
cp /tmp/rendered/nginx_vhost.conf "/etc/nginx/sites-available/${SITE_URL}"
echo "  [OK] /etc/nginx/sites-available/${SITE_URL}"

# ── Section K: DH params + enable site ───────────────────────────────
echo "=== K: DH params + enable site ==="
if [ ! -f "${NGINX_DHPARAM}" ]; then
    echo "  Generating DH params (2048-bit) — once per VM, reused on redeploy ..."
    openssl dhparam -out "${NGINX_DHPARAM}" 2048 2>/dev/null
    echo "  [OK] DH params written to ${NGINX_DHPARAM}"
else
    echo "  [OK] DH params already present — skipping"
fi
ln -sf "/etc/nginx/sites-available/${SITE_URL}" "/etc/nginx/sites-enabled/${SITE_URL}"
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo "  [OK] nginx reloaded with SSL site"
