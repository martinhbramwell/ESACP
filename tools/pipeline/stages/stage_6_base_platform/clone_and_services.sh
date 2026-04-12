#!/usr/bin/env bash
set -euo pipefail

# Stage 6b: Clone apps + start services (sections A2d, A3, A3b, B2b)
# Usage: sudo bash clone_and_services.sh BENCH_DIR ERP_USER

BENCH_DIR="$1"
ERP_USER="$2"

_GH_CLONE() {
    sudo -u "$ERP_USER" bash -c "
        export DISPLAY=:0
        export SSH_ASKPASS=/home/$ERP_USER/.ssh/gh_askpass.sh
        export SSH_ASKPASS_REQUIRE=force
        export GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=no'
        $1
    "
}

echo "=== A2d: clone apps from GitHub ==="
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
if [ ! -d "$BENCH_DIR/BaRe/.git" ]; then
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && git clone https://github.com/martinhbramwell/BaRe.git BaRe"
    echo "  [OK] BaRe cloned"
else
    sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR/BaRe && git checkout main && git pull"
    echo "  [OK] BaRe pulled"
fi
echo "  [OK] all apps cloned/pulled"

echo "=== A3: start bench services (supervisor) ==="
cp /tmp/rendered/stop.py "$BENCH_DIR/stop.py"
chown "$ERP_USER:$ERP_USER" "$BENCH_DIR/stop.py"
chmod 755 "$BENCH_DIR/stop.py"
echo "  Stopping stale bench/honcho processes..."
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && python3 stop.py"
sudo supervisorctl stop all 2>/dev/null || true
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup supervisor --yes"
sudo cp "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf

echo "=== A3b: deploy ce_sri_svc supervisor conf ==="
sudo cp /tmp/rendered/ce_sri_svc_supervisor.conf /etc/supervisor/conf.d/ce-sri-svc.conf
echo "  [OK] /etc/supervisor/conf.d/ce-sri-svc.conf deployed"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all || true
echo "  Waiting 20s for Redis to be ready..."
sleep 20
echo "  [OK] bench services started"
sudo chmod o+x "/home/$ERP_USER"
echo "  [OK] /home/$ERP_USER world-traversable for nginx"

echo "=== B2b: npm install for ce_sri_svc ==="
_CESRI_SVC="$BENCH_DIR/apps/ce_sri/services/ce_sri_svc"
if [ -f "$_CESRI_SVC/package.json" ]; then
    sudo -u "$ERP_USER" bash -c "cd $_CESRI_SVC && npm install 2>&1"
    echo "  [OK] npm install completed for ce_sri_svc"
else
    echo "  [SKIP] no package.json in ce_sri_svc"
fi
