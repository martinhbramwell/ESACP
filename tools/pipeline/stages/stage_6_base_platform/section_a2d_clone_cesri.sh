#!/usr/bin/env bash
set -euo pipefail

# Section A2d (ce_sri family): clone ce_sri / route_planner / returnable / ce_sri_svc (gated)
# Usage: section_a2d_clone_cesri.sh BENCH_DIR ERP_USER PROVISION_MODE

BENCH_DIR="$1"
ERP_USER="$2"
PROVISION_MODE="${3:-restored}"

echo "=== A2d (ce_sri family): clone apps from GitHub ==="
if [ "$PROVISION_MODE" = "generic" ]; then
    echo "  [SKIP] ce_sri / route_planner / returnable / ce_sri_svc — generic mode"
    exit 0
fi

_GH_CLONE() {
    sudo -u "$ERP_USER" bash -c "
        export DISPLAY=:0
        export SSH_ASKPASS=/home/$ERP_USER/.ssh/gh_askpass.sh
        export SSH_ASKPASS_REQUIRE=force
        export GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=no'
        $1
    "
}

if [ ! -d "$BENCH_DIR/apps/ce_sri/.git" ]; then
    _GH_CLONE "cd $BENCH_DIR && git clone git@ce_sri.gh:martinhbramwell/ce_sri.git apps/ce_sri --branch wip/2026-03-25"
    echo "  [OK] ce_sri cloned"
else
    _GH_CLONE "cd $BENCH_DIR/apps/ce_sri && git pull"
    echo "  [OK] ce_sri pulled"
fi
if [ ! -d "$BENCH_DIR/apps/route_planner/.git" ]; then
    _GH_CLONE "cd $BENCH_DIR && git clone git@route_planner.gh:martinhbramwell/route_planner.git apps/route_planner --branch wip/2026-03-31"
    echo "  [OK] route_planner cloned"
else
    _GH_CLONE "cd $BENCH_DIR/apps/route_planner && git pull"
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
    _GH_CLONE "mkdir -p $BENCH_DIR/apps/ce_sri/services && cd $BENCH_DIR && git clone git@ce_sri_svc.gh:martinhbramwell/ce_sri_svc.git apps/ce_sri/services/ce_sri_svc --branch wip/2026-03-31"
    echo "  [OK] ce_sri_svc cloned"
else
    _GH_CLONE "cd $BENCH_DIR/apps/ce_sri/services/ce_sri_svc && git pull"
    echo "  [OK] ce_sri_svc pulled"
fi
