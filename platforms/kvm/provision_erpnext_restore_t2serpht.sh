#!/usr/bin/env bash
#
# provision_erpnext_restore_t2serpht.sh
# Run from Mighty (controller) — not from saconsole or target.
#
# Full A→Z ERPNext restore for target2 (stg.erpnext.host / serpht):
#   rsyncs bespoke apps + BaRe + backup to target2,
#   places apikey.sh and socials_google.json,
#   installs apps into the bench venv, then runs the database restore
#   (including social login config via ERPNext REST API).
#
# Prerequisites:
#   - target2 is at the "ERPNext v13 Installed" snapshot
#     (bench with frappe + erpnext only, no bespoke apps, no production data)
#     WireGuard mesh must be up: you@10.10.0.4 reachable
#   - ~/projects/Logichem/ce_sri_prod/ce_sri          (bespoke app)
#   - ~/projects/Logichem/returnable_prod/returnable   (bespoke app)
#   - ~/projects/Logichem/route_planner_prod/route_planner (bespoke app)
#   - ~/projects/Logichem/ce_sri/BKP/BACKUP.txt        (backup file name)
#   - ~/projects/Logichem/ce_sri/BKP/<backup>.tgz      (backup archive)
#   - ~/projects/Logichem/envars_serpht_restore.sh     (site + restore config)
#
# Usage:
#   bash platforms/kvm/provision_erpnext_restore_t2serpht.sh [--fresh]
#
#   --fresh   Revert target2 to "ERPNext v13 Installed" snapshot before starting.
#             NOTE: If that snapshot does not yet exist, run prepareServer_0_serpht.sh
#             on saconsole first, then take the snapshot manually.
#             Omit --fresh if you already reverted manually.
#
set -euo pipefail

LOGICHEM_DIR="${HOME}/projects/Logichem"
source "${LOGICHEM_DIR}/envars_serpht_restore.sh"

TARGET_SSH="you@10.10.0.4"
ERP_USER="adm"
TARGET_BENCH_REMOTE="/home/${ERP_USER}/${TARGET_BENCH_NAME}"
RSYNC_OPTS=(-a --delete --exclude='*.egg-info' --rsync-path="sudo rsync")

CE_SRI_SRC="${LOGICHEM_DIR}/ce_sri_prod"
RETURNABLE_SRC="${LOGICHEM_DIR}/returnable_prod"
ROUTE_PLANNER_SRC="${LOGICHEM_DIR}/route_planner_prod"
BARE_SRC="${LOGICHEM_DIR}/BaRe"
BKP_SRC="${LOGICHEM_DIR}/ce_sri/BKP"
EXAMPLE_FILES="${LOGICHEM_DIR}/ce_sri/example_srvr_files"

# ── Phase 0: optional snapshot revert ─────────────────────────────────────────
if [[ "${1:-}" == "--fresh" ]]; then
    echo "=== Phase 0: reverting target2 to 'ERPNext v13 Installed' snapshot ==="
    # NOTE: verify this snapshot name matches what was taken after prepareServer_0_serpht.sh
    ssh hasan@toshy "virsh --connect qemu:///system snapshot-revert target2 \
        'ERPNext v13 Installed' --running"
    echo "  Waiting for target2 WireGuard to come up (up to 90s)..."
    for i in $(seq 1 18); do
        ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -q ${TARGET_SSH} true 2>/dev/null \
            && echo "  target2 is up" && break
        echo "  ... attempt ${i}/18"; sleep 5
    done
fi

# ── Phase 1: rsync bespoke app code ───────────────────────────────────────────
echo ""
echo "=== Phase 1: rsyncing bespoke apps to target2 ==="
for pair in \
    "${CE_SRI_SRC}:${TARGET_BENCH_REMOTE}/apps/ce_sri" \
    "${RETURNABLE_SRC}:${TARGET_BENCH_REMOTE}/apps/returnable" \
    "${ROUTE_PLANNER_SRC}:${TARGET_BENCH_REMOTE}/apps/route_planner"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    echo "  rsync $(basename ${src}) → ${TARGET_SSH}:${dst}"
    rsync "${RSYNC_OPTS[@]}" "${src}/" "${TARGET_SSH}:${dst}/"
done

# Fix ownership — rsync via sudo rsync writes files as root; adm needs to own them
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A \
    chown -R ${ERP_USER}:${ERP_USER} ${TARGET_BENCH_REMOTE}/apps/"
echo "  ... ownership set to ${ERP_USER} on apps/"

# ── Phase 2: rsync BaRe scripts ───────────────────────────────────────────────
echo ""
echo "=== Phase 2: rsyncing BaRe to target2 ==="
rsync -a --rsync-path="sudo rsync" "${BARE_SRC}/" "${TARGET_SSH}:${TARGET_BENCH_REMOTE}/BaRe/"
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A \
    chown -R ${ERP_USER}:${ERP_USER} ${TARGET_BENCH_REMOTE}/BaRe/"
echo "  ... ownership set to ${ERP_USER} on BaRe/"

# ── Phase 3: rsync backup ─────────────────────────────────────────────────────
echo ""
echo "=== Phase 3: rsyncing backup to target2 ==="
rsync -a --rsync-path="sudo rsync" "${BKP_SRC}/" "${TARGET_SSH}:${TARGET_BENCH_REMOTE}/BKP/"
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A \
    chown -R ${ERP_USER}:${ERP_USER} ${TARGET_BENCH_REMOTE}/BKP/"
echo "  ... ownership set to ${ERP_USER} on BKP/"
echo "  Backup: $(cat ${BKP_SRC}/BACKUP.txt)"

# ── Phase 3.5: place apikey.sh and socials_google.json ────────────────────────
echo ""
echo "=== Phase 3.5: placing apikey.sh and socials_google.json on target2 ==="

SITE_DIR="${TARGET_BENCH_REMOTE}/sites/${ERPNEXT_SITE_URL}"
PRIVATE_FILES="${SITE_DIR}/private/files"

# Ensure private/files directory exists (created by bench new-site, but be safe)
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A -u ${ERP_USER} mkdir -p ${PRIVATE_FILES}"

# Create apikey.sh — stores API key for handleRestore.sh → restoreSocialLoginConfig()
# Keys are for the Administrator user in the production DB (valid after DB restore)
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A -u ${ERP_USER} bash -c \
    'echo \"export KEYS=\\\"${KEYS}\\\"\" > ${PRIVATE_FILES}/apikey.sh && \
     chmod 600 ${PRIVATE_FILES}/apikey.sh'"
echo "  ... apikey.sh placed at ${PRIVATE_FILES}/apikey.sh"

# Place socials_google.json at bench/sites/stg.erpnext.host/ (NOT private/files/)
# handleRestore.sh looks for: ../sites/${ERPNEXT_SITE_URL}/socials_google.json
# relative to BaRe/ inside the bench
scp "${EXAMPLE_FILES}/socials_google.json" "${TARGET_SSH}:/tmp/socials_google.json"
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A -u ${ERP_USER} \
    cp /tmp/socials_google.json ${SITE_DIR}/socials_google.json && \
    rm /tmp/socials_google.json"
echo "  ... socials_google.json placed at ${SITE_DIR}/socials_google.json"

# Place ddlViews.sql — installApps.sh copies from apps/ce_sri/example_srvr_files/views.ddl
# but ce_sri_prod has no example_srvr_files; place it directly from the dev repo (#29)
VIEWS_DDL="${LOGICHEM_DIR}/ce_sri/example_srvr_files/views.ddl"
scp "${VIEWS_DDL}" "${TARGET_SSH}:/tmp/ddlViews.sql"
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A -u ${ERP_USER} \
    cp /tmp/ddlViews.sql ${PRIVATE_FILES}/ddlViews.sql && \
    rm /tmp/ddlViews.sql"
echo "  ... ddlViews.sql placed at ${PRIVATE_FILES}/ddlViews.sql"

# ── Phase 4: push envars.sh to /opt/ce_sri/ on target2 ───────────────────────
echo ""
echo "=== Phase 4: pushing envars_serpht_restore.sh to target2 /opt/ce_sri/envars.sh ==="
scp "${LOGICHEM_DIR}/envars_serpht_restore.sh" "${TARGET_SSH}:/tmp/envars_serpht.sh"
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A \
    cp /tmp/envars_serpht.sh /opt/ce_sri/envars.sh && \
    rm /tmp/envars_serpht.sh"
echo "  ... /opt/ce_sri/envars.sh updated on target2"

# ── Phase 5: install apps, migrate, place ddlViews.sql ───────────────────────
echo ""
echo "=== Phase 5: installApps.sh (running on target2 as ${ERP_USER}) ==="
ssh ${TARGET_SSH} "sudo -u ${ERP_USER} bash -c 'cd ${TARGET_BENCH_REMOTE} && bash BaRe/installApps.sh'"

# ── Phase 6: restore database, views, social logins ──────────────────────────
echo ""
echo "=== Phase 6: handleRestore.sh (running on target2 as ${ERP_USER}) ==="
ssh ${TARGET_SSH} "sudo -u ${ERP_USER} bash -c 'cd ${TARGET_BENCH_REMOTE} && bash BaRe/handleRestore.sh'"

# ── Phase 7: restart bench ────────────────────────────────────────────────────
echo ""
echo "=== Phase 7: restarting bench on target2 ==="
ssh ${TARGET_SSH} "sudo -u ${ERP_USER} bash -c \
    'cd ${TARGET_BENCH_REMOTE} && \
     SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A supervisorctl restart all 2>/dev/null || \
     bench restart 2>/dev/null || true'"
echo "  ... bench restarted"

echo ""
echo "============================================================"
echo " provision_erpnext_restore_t2serpht.sh complete"
echo " ERPNext staging: https://${ERPNEXT_SITE_URL}"
echo " WireGuard: target2 at 10.10.0.4"
echo ""
echo " Next steps:"
echo "   1. Browser-verify login at https://${ERPNEXT_SITE_URL}"
echo "   2. Test social login (Google)"
echo "   3. Take snapshot 'ERPNext v13 Production DB Restored' on target2"
echo "   4. Test SRI electronic voucher connection (.p12 + ce_sri_parms.json)"
echo "============================================================"
