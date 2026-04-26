#!/usr/bin/env bash
set -euo pipefail

# Section A3 + A3b: bench setup supervisor + (optional) ce_sri_svc supervisor conf
# Usage: section_a3_supervisor.sh BENCH_DIR ERP_USER PROVISION_MODE

BENCH_DIR="$1"
ERP_USER="$2"
PROVISION_MODE="${3:-restored}"

echo "=== A3: start bench services (supervisor) ==="
cp /tmp/rendered/stop.py "$BENCH_DIR/stop.py"
chown "$ERP_USER:$ERP_USER" "$BENCH_DIR/stop.py"
chmod 755 "$BENCH_DIR/stop.py"
echo "  Stopping stale bench/honcho processes..."
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && python3 stop.py"
sudo supervisorctl stop all 2>/dev/null || true
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup supervisor --yes"
sudo cp "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf

if [ "$PROVISION_MODE" = "generic" ]; then
    echo "=== A3b: skip ce_sri_svc supervisor conf — generic mode ==="
else
    echo "=== A3b: deploy ce_sri_svc supervisor conf ==="
    sudo cp /tmp/rendered/ce_sri_svc_supervisor.conf /etc/supervisor/conf.d/ce-sri-svc.conf
    echo "  [OK] /etc/supervisor/conf.d/ce-sri-svc.conf deployed"
fi

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all || true
echo "  Waiting 20s for Redis to be ready..."
sleep 20
echo "  [OK] bench services started"
sudo chmod o+x "/home/$ERP_USER"
echo "  [OK] /home/$ERP_USER world-traversable for nginx"
