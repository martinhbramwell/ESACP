#!/usr/bin/env bash
set -euo pipefail

# Stage 8b: Post-restart app configuration (sections H4e, H4f, H4f-poll, H4g)
# Usage: sudo bash post_restart_config.sh BENCH_DIR SITE_URL ERP_USER GUNICORN_PORT

BENCH_DIR="$1"
SITE_URL="$2"
ERP_USER="$3"
GUNICORN_PORT="$4"

echo "=== H4e: generate .env via UPDATE_SRI_SERVICE_PARAMETERS.py ==="
_CESRI_SVC="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
python3 /tmp/vm_scripts/h4e_patch_parms.py \
  --apikey-sh "$BENCH_DIR/sites/$SITE_URL/private/files/apikey.sh" \
  --parms "/home/$ERP_USER/.ssh/secrets/ce_sri_parms.json"
sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && python3 UPDATE_SRI_SERVICE_PARAMETERS.py --parms /home/$ERP_USER/.ssh/secrets/ce_sri_parms.json"
echo "  [OK] .env generated for $SITE_URL"

echo "=== H4f: restart after .env changes ==="
sudo supervisorctl reread
sudo supervisorctl update
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && python3 stop.py"
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart"
sudo supervisorctl restart frappe-bench-ce-sri-svc
sudo nginx -t && sudo systemctl reload nginx
echo "  [OK] services restarted"

echo "=== H4f-poll: wait for gunicorn after restart ==="
python3 /tmp/vm_scripts/poll_gunicorn.py \
  --url "http://$SITE_URL:$GUNICORN_PORT/api/method/ping" \
  --timeout 120

echo "=== H4g: install_specific.py after-restart (API config) ==="
export TARGET_BENCH="$BENCH_DIR" ERPNEXT_SITE_URL="$SITE_URL"
sudo -u "$ERP_USER" -E bash -c "cd $BENCH_DIR && python3 /tmp/install_specific.py after-restart"
echo "  [OK] after-restart complete"
