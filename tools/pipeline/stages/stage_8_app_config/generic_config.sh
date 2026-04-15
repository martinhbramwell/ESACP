#!/usr/bin/env bash
set -euo pipefail

# Stage 8 (generic mode): Minimal app config — no ce_sri, no production secrets.
# Usage: sudo bash generic_config.sh BENCH_DIR SITE_URL ERP_USER ERP_USER_PWD GUNICORN_PORT

BENCH_DIR="$1"
SITE_URL="$2"
ERP_USER="$3"
ERP_USER_PWD="$4"
GUNICORN_PORT="$5"

echo "=== H: supervisor reload ==="
sudo supervisorctl reread
sudo supervisorctl update
echo "  [OK] supervisor updated"

echo "=== H2a: ensure site hostname resolves to localhost ==="
if ! grep -q "$SITE_URL" /etc/hosts; then
    echo "127.0.0.1 $SITE_URL" | sudo tee -a /etc/hosts >/dev/null
    echo "  [OK] added $SITE_URL to /etc/hosts"
else
    echo "  [OK] $SITE_URL already in /etc/hosts"
fi

echo "=== H2: bench restart ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart"
echo "  [OK] bench restarted"

echo "=== H2b: wait for gunicorn ==="
python3 /tmp/vm_scripts/poll_gunicorn.py \
  --url "http://$SITE_URL:$GUNICORN_PORT/api/method/ping" \
  --timeout 120

echo "=== H4c: generate bench nginx.conf ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup nginx --yes"
sudo nginx -t && sudo systemctl reload nginx
echo "  [OK] nginx configured and reloaded"

echo "=== Generic app config complete — wizard ready ==="
