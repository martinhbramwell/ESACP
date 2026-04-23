#!/usr/bin/env bash
set -euo pipefail
# Section A2d (bespoke): clone/pull ce_sri, route_planner, returnable, ce_sri_svc.
# Restore-mode only. Orchestrator must skip this when MODE=generic.
# Needs env: BENCH_DIR, ERP_USER
source "$(dirname "$0")/_helpers.sh"

echo "=== A2d (bespoke): clone ce_sri / route_planner / returnable / ce_sri_svc ==="

if [ ! -d "$BENCH_DIR/apps/ce_sri/.git" ]; then
    _gh_clone "cd $BENCH_DIR && git clone git@ce_sri.gh:martinhbramwell/ce_sri.git apps/ce_sri --branch wip/2026-03-25"
    echo "  [OK] ce_sri cloned"
else
    _gh_clone "cd $BENCH_DIR/apps/ce_sri && git pull"
    echo "  [OK] ce_sri pulled"
fi

if [ ! -d "$BENCH_DIR/apps/route_planner/.git" ]; then
    _gh_clone "cd $BENCH_DIR && git clone git@route_planner.gh:martinhbramwell/route_planner.git apps/route_planner --branch wip/2026-03-31"
    echo "  [OK] route_planner cloned"
else
    _gh_clone "cd $BENCH_DIR/apps/route_planner && git pull"
    echo "  [OK] route_planner pulled"
fi

if [ ! -d "$BENCH_DIR/apps/returnable/.git" ]; then
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && git clone https://github.com/martinhbramwell/BtlMng.git apps/returnable --branch wip/2026-03-31"
    echo "  [OK] returnable (BtlMng) cloned"
else
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR/apps/returnable && git pull"
    echo "  [OK] returnable pulled"
fi

if [ ! -d "$BENCH_DIR/apps/ce_sri/services/ce_sri_svc/.git" ]; then
    _gh_clone "mkdir -p $BENCH_DIR/apps/ce_sri/services && cd $BENCH_DIR && git clone git@ce_sri_svc.gh:martinhbramwell/ce_sri_svc.git apps/ce_sri/services/ce_sri_svc --branch wip/2026-03-31"
    echo "  [OK] ce_sri_svc cloned"
else
    _gh_clone "cd $BENCH_DIR/apps/ce_sri/services/ce_sri_svc && git pull"
    echo "  [OK] ce_sri_svc pulled"
fi
