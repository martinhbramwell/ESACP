#!/usr/bin/env bash
set -euo pipefail

# Stage 8a: Pre-restart app configuration (sections H, H2a, H2, H2b, H4a, H3, H4b, H4c, H4d)
# Usage: sudo bash pre_restart_config.sh BENCH_DIR SITE_URL ERP_USER ERP_USER_PWD GUNICORN_PORT

BENCH_DIR="$1"
SITE_URL="$2"
ERP_USER="$3"
ERP_USER_PWD="$4"
GUNICORN_PORT="$5"

echo "=== H: supervisor reload (post-restore) ==="
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
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && python3 stop.py"
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart"
sudo supervisorctl restart frappe-bench-ce-sri-svc
echo "  [OK] bench + ce_sri_svc restarted"

echo "=== H2b: wait for gunicorn ==="
python3 /tmp/vm_scripts/poll_gunicorn.py \
  --url "http://$SITE_URL:$GUNICORN_PORT/api/method/ping" \
  --timeout 120

echo "=== H4a: clear stale encrypted secrets + regenerate API key ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && $BENCH_DIR/env/bin/python /tmp/vm_scripts/h4a_apikeys.py --site $SITE_URL --bench-dir $BENCH_DIR"

echo "=== H3: reset admin password (H4a wipes __Auth — must run after) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL set-admin-password $ERP_USER_PWD"
echo "  [OK] admin password reset"

echo "=== H4b: place secrets for install.py ==="
sudo -u "$ERP_USER" mkdir -p "/home/$ERP_USER/.ssh/secrets"
for f in /tmp/*.p12 /tmp/ce_sri_parms_*.json /tmp/docType_Logo.png; do
  if [ -f "$f" ]; then
    DEST="/home/$ERP_USER/.ssh/secrets/$(basename "$f")"
    if [[ "$f" == *ce_sri_parms_*.json ]]; then
      DEST="/home/$ERP_USER/.ssh/secrets/ce_sri_parms.json"
    fi
    sudo mv "$f" "$DEST"
    sudo chown "$ERP_USER:$ERP_USER" "$DEST"
    sudo chmod 600 "$DEST"
    echo "  [OK] $(basename "$DEST") -> secrets/"
  fi
done

echo "=== H4c: generate bench nginx.conf ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup nginx --yes"
echo "  [OK] config/nginx.conf generated"

echo "=== H4d: install_specific.py before-install (file patches) ==="
export TARGET_BENCH="$BENCH_DIR" ERPNEXT_SITE_URL="$SITE_URL"
sudo -u "$ERP_USER" -E bash -c "cd $BENCH_DIR && python3 /tmp/install_specific.py before-install"
echo "  [OK] before-install complete"
