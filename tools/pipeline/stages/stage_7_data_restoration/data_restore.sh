#!/usr/bin/env bash
# Stage 7: Data Restoration — sections D through G2.
#
# Usage: sudo bash data_restore.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>
set -euo pipefail

BENCH_DIR="${1:?Usage: data_restore.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
SITE_URL="${2:?Usage: data_restore.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
ERP_USER="${3:?Usage: data_restore.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
MYPWD="${4:?Usage: data_restore.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"
ERP_USER_PWD="${5:?Usage: data_restore.sh <bench_dir> <site_url> <erp_user> <mypwd> <erp_user_pwd>}"

echo "=== D: bench new-site + install-app erpnext ==="
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

echo "=== E: place ddlViews.sql ==="
sudo -u "$ERP_USER" mkdir -p "$BENCH_DIR/sites/$SITE_URL/private/files"
sudo -u "$ERP_USER" cp /tmp/ddlViews.sql "$BENCH_DIR/sites/$SITE_URL/private/files/ddlViews.sql"
rm -f /tmp/ddlViews.sql
echo "  [OK] ddlViews.sql placed"

echo "=== E1: seed tabPatch Log (skip patches that crash on restored DB) ==="
python3 /tmp/vm_scripts/g1_seed_patch_log.py --bench-dir "$BENCH_DIR" --site "$SITE_URL"

echo "=== F: installApps.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/installApps.sh"
echo "  [OK] installApps.sh complete"

echo "=== G-pre: strip DEFINER clauses from backup SQL ==="
python3 /tmp/vm_scripts/gpre_strip_definer.py --bench-dir "$BENCH_DIR"

echo "=== G: handleRestore.sh (social login deferred to post-H4a) ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && DEFER_SOCIAL_LOGIN=1 bash BaRe/handleRestore.sh"
echo "  [OK] database restored"

echo "=== G1: re-seed tabPatch Log (restore wiped DB) ==="
python3 /tmp/vm_scripts/g1_seed_patch_log.py --bench-dir "$BENCH_DIR" --site "$SITE_URL"

echo "=== G2: clear fixture Custom Fields + re-migrate ==="
echo "  Clearing fixture-defined Custom Fields from restored DB..."
python3 /tmp/vm_scripts/g2_clear_fixture_custom_fields.py --bench-dir "$BENCH_DIR" --site "$SITE_URL"
echo "  Re-running bench migrate to reimport fixtures..."
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL migrate" 2>&1 \
  | grep -E "^(Migrating|Executing|Updating|Building)" | tail -10
echo "  [OK] fixtures reimported with correct positioning"
