#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="/home/adm/frappe-bench"
SITE_URL="lab.target3.local"
ERP_USER="adm"
MYPWD="erpnext_build"
ERP_USER_PWD="sasa"

echo "=== A: /opt/ce_sri/ + envars.sh ==="
sudo mkdir -p /opt/ce_sri
sudo chmod 755 /opt/ce_sri
sudo tee /opt/ce_sri/envars.sh > /dev/null << 'ENVEOF'
#!/usr/bin/env bash
export ERP_USER_PWD="sasa"
export MYPWD="erpnext_build"
export ERPNEXT_SITE="lab"
export ERPNEXT_DNS="target3"
export ERPNEXT_TLD="local"
export ERPNEXT_DOMAIN="target3.local"
export ERPNEXT_SITE_URL="lab.target3.local"
export ERP_USER_NAME="adm"
export ERPNEXT_SITE_NICKNAME="TPL"
export TARGET_BENCH_NAME="frappe-bench"
export TARGET_BENCH="$HOME/frappe-bench"
export RESTORE_SITE_CONFIG="no"
export KEEP_SITE_PASSWORD="yes"
ENVEOF
sudo chmod 644 /opt/ce_sri/envars.sh
echo "  [OK] /opt/ce_sri/envars.sh"

echo "=== B: fix ownership of rsynced dirs ==="
sudo chown -R "$ERP_USER:$ERP_USER" /home/adm/frappe-bench/apps/ce_sri /home/adm/frappe-bench/apps/returnable /home/adm/frappe-bench/apps/route_planner /home/adm/frappe-bench/BaRe /home/adm/frappe-bench/BKP
echo "  [OK] ownership -> $ERP_USER"

echo "=== C: BaRe/envars.sh symlink ==="
sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
echo "  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh"

echo "=== D: bench new-site + install-app erpnext ==="
echo "  site: $SITE_URL  bench: $BENCH_DIR"
sudo -u "$ERP_USER" bash -c "
  cd $BENCH_DIR
  bench new-site $SITE_URL \
    --mariadb-root-password $MYPWD \
    --admin-password $ERP_USER_PWD
  bench --site $SITE_URL install-app erpnext
"
echo "  [OK] site created, erpnext installed"

echo "=== E: place ddlViews.sql ==="
sudo -u "$ERP_USER" mkdir -p "$BENCH_DIR/sites/$SITE_URL/private/files"
  sudo -u adm cp /tmp/ddlViews.sql /home/adm/frappe-bench/sites/lab.target3.local/private/files/ddlViews.sql
  rm -f /tmp/ddlViews.sql
  echo '  [OK] ddlViews.sql placed'

echo "=== F: installApps.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/installApps.sh"
echo "  [OK] installApps.sh complete"

echo "=== G-pre: strip DEFINER clauses from backup SQL ==="
_BKP_ARCHIVE=$(tr -d '\r\n' < "$BENCH_DIR/BKP/BACKUP.txt")
_BKP_PATH="$BENCH_DIR/BKP/$_BKP_ARCHIVE"
_SQL_ENTRY="${_BKP_ARCHIVE%.tgz}-database.sql.gz"
_WORK="/tmp/_definer_strip"
rm -rf "$_WORK" && mkdir -p "$_WORK"
tar -xzf "$_BKP_PATH" -C "$_WORK"
gunzip -c "$_WORK/$_SQL_ENTRY" \
  | sed 's/DEFINER=[^ ]*/DEFINER=CURRENT_USER/g' \
  | gzip > "$_WORK/${_SQL_ENTRY}.clean"
mv "$_WORK/${_SQL_ENTRY}.clean" "$_WORK/$_SQL_ENTRY"
(cd "$_WORK" && tar -czf "$_BKP_PATH" -- *)
rm -rf "$_WORK"
echo "  [OK] DEFINER stripped from $_SQL_ENTRY"

echo "=== G: handleRestore.sh ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bash BaRe/handleRestore.sh"
echo "  [OK] database restored"

echo "=== G2: clear fixture Custom Fields + re-migrate ==="
echo "  Clearing fixture-defined Custom Fields from restored DB..."
python3 /tmp/vm_scripts/g2_clear_fixture_custom_fields.py \
  --bench-dir "$BENCH_DIR" --site "$SITE_URL"
echo "  Re-running bench migrate to reimport fixtures..."
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench --site $SITE_URL migrate" 2>&1 \
  | grep -E "^(Migrating|Executing|Updating|Building)" | tail -10
echo "  [OK] fixtures reimported with correct positioning"

echo "=== H: bench restart ==="
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench restart || true"
echo "  [OK] bench restarted"
