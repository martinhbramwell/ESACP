#!/usr/bin/env bash
#
# provision_erpnext_restore.sh
# Run from Mighty (controller) — not from saconsole or target.
#
# Full A→Z ERPNext lab restore: rsyncs apps + BaRe + backup to target1,
# installs apps into the bench venv, then runs the database restore.
#
# Prerequisites:
#   - target1 is at the "ERPNext v13 Installed" snapshot
#     (bench with frappe + erpnext only, no bespoke apps, no production data)
#   - ~/projects/Logichem/ce_sri_prod/ce_sri          (bespoke app)
#   - ~/projects/Logichem/returnable_prod/returnable   (bespoke app)
#   - ~/projects/Logichem/route_planner_prod/route_planner (bespoke app)
#   - ~/projects/Logichem/ce_sri/BKP/BACKUP.txt        (backup file name)
#   - ~/projects/Logichem/ce_sri/BKP/<backup>.tgz      (backup archive)
#   - ~/projects/Logichem/envars.sh                    (site + restore config)
#   - WireGuard mesh up: you@10.10.0.3 reachable
#
# Usage:
#   bash platforms/kvm/provision_erpnext_restore.sh [--fresh]
#
#   --fresh   Revert target1 to "ERPNext v13 Installed" snapshot before starting.
#             Omit if you already reverted manually.
#
set -euo pipefail

LOGICHEM_DIR="${HOME}/projects/Logichem"
source "${LOGICHEM_DIR}/envars.sh"

TARGET_SSH="you@10.10.0.3"
ERP_USER="adm"
TARGET_BENCH_REMOTE="/home/${ERP_USER}/${TARGET_BENCH_NAME}"
RSYNC_OPTS=(-a --delete --rsync-path="sudo rsync")

CE_SRI_SRC="${LOGICHEM_DIR}/ce_sri_prod"
RETURNABLE_SRC="${LOGICHEM_DIR}/returnable_prod"
ROUTE_PLANNER_SRC="${LOGICHEM_DIR}/route_planner_prod"
BARE_SRC="${LOGICHEM_DIR}/BaRe"
BKP_SRC="${LOGICHEM_DIR}/ce_sri/BKP"

# ── Phase 0: optional snapshot revert ─────────────────────────────────────────
if [[ "${1:-}" == "--fresh" ]]; then
    echo "=== Phase 0: reverting target1 to 'ERPNext v13 Installed' snapshot ==="
    ssh hasan@toshy "virsh --connect qemu:///system snapshot-revert target1 \
        'ERPNext v13 Installed' --running"
    echo "  Waiting for target1 WireGuard to come up (up to 90s)..."
    for i in $(seq 1 18); do
        ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -q ${TARGET_SSH} true 2>/dev/null \
            && echo "  target1 is up" && break
        echo "  ... attempt ${i}/18"; sleep 5
    done
fi

# ── Phase 1: rsync bespoke app code ───────────────────────────────────────────
echo ""
echo "=== Phase 1: rsyncing bespoke apps to target1 ==="
for pair in \
    "${CE_SRI_SRC}:${TARGET_BENCH_REMOTE}/apps/ce_sri" \
    "${RETURNABLE_SRC}:${TARGET_BENCH_REMOTE}/apps/returnable" \
    "${ROUTE_PLANNER_SRC}:${TARGET_BENCH_REMOTE}/apps/route_planner"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    echo "  rsync $(basename ${src}) → ${TARGET_SSH}:${dst}"
    rsync "${RSYNC_OPTS[@]}" "${src}/" "${TARGET_SSH}:${dst}/"
done

# ── Phase 2: rsync BaRe scripts ───────────────────────────────────────────────
echo ""
echo "=== Phase 2: rsyncing BaRe to target1 ==="
rsync -a --rsync-path="sudo rsync" "${BARE_SRC}/" "${TARGET_SSH}:${TARGET_BENCH_REMOTE}/BaRe/"

# ── Phase 3: rsync backup ─────────────────────────────────────────────────────
echo ""
echo "=== Phase 3: rsyncing backup to target1 ==="
rsync -a --rsync-path="sudo rsync" "${BKP_SRC}/" "${TARGET_SSH}:${TARGET_BENCH_REMOTE}/BKP/"
echo "  Backup: $(cat ${BKP_SRC}/BACKUP.txt)"

# ── Phase 4: push envars.sh to /opt/ce_sri/ ───────────────────────────────────
echo ""
echo "=== Phase 4: pushing envars.sh ==="
scp "${LOGICHEM_DIR}/envars.sh" "${TARGET_SSH}:/tmp/envars_lab.sh"
ssh ${TARGET_SSH} "SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A cp /tmp/envars_lab.sh /opt/ce_sri/envars.sh && rm /tmp/envars_lab.sh"
echo "  ... /opt/ce_sri/envars.sh updated"

# ── Phase 5: install apps, migrate, place ddlViews.sql ───────────────────────
echo ""
echo "=== Phase 5: installApps.sh (running on target1 as ${ERP_USER}) ==="
ssh ${TARGET_SSH} "sudo -u ${ERP_USER} bash -c 'cd ${TARGET_BENCH_REMOTE} && bash BaRe/installApps.sh'"

# ── Phase 6: restore database ─────────────────────────────────────────────────
echo ""
echo "=== Phase 6: handleRestore.sh (running on target1 as ${ERP_USER}) ==="
ssh ${TARGET_SSH} "sudo -u ${ERP_USER} bash -c 'cd ${TARGET_BENCH_REMOTE} && bash BaRe/handleRestore.sh'"

echo ""
echo "============================================================"
echo " provision_erpnext_restore.sh complete"
echo " ERPNext lab: https://${ERPNEXT_SITE_URL}"
echo " Pending: test SRI electronic voucher connection"
echo "============================================================"
