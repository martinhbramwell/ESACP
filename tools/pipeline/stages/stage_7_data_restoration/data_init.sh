#!/usr/bin/env bash
# Stage 7 (generic mode): Create a blank ERPNext site — no DB restore.
#
# Usage: sudo bash data_init.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>
set -euo pipefail

BENCH_DIR="${1:?Usage: data_init.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
SITE_URL="${2:?Usage: data_init.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
ERP_USER="${3:?Usage: data_init.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
MYPWD="${4:?Usage: data_init.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
ERP_USER_PWD="${5:?Usage: data_init.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"

echo "=== D: bench new-site + install-app erpnext (generic) ==="
echo "  site: $SITE_URL  bench: $BENCH_DIR"
if sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL doctor" 2>/dev/null; then
  echo "  [SKIP] site $SITE_URL already exists"
else
  sudo -u "$ERP_USER" bash -c "
    cd $BENCH_DIR
    bench new-site $SITE_URL \
      --mariadb-root-password $MYPWD \
      --admin-password $ERP_USER_PWD
    bench --site $SITE_URL install-app erpnext
  "
  echo "  [OK] site created, erpnext installed"
fi

echo "=== D1: ensure currentsite.txt ==="
sudo -u "$ERP_USER" bash -c "echo '$SITE_URL' > $BENCH_DIR/sites/currentsite.txt"
echo "  [OK] currentsite.txt set to $SITE_URL"

echo "=== Generic site ready — setup wizard will run on first browser visit ==="
