#!/usr/bin/env bash
set -euo pipefail
# Section A3: stop stale processes, set up bench supervisor, start all.
# Unchanged across modes.
# Needs env: BENCH_DIR, ERP_USER
echo "=== A3: start bench services (supervisor) ==="
cp /tmp/rendered/stop.py "$BENCH_DIR/stop.py"
chown "$ERP_USER:$ERP_USER" "$BENCH_DIR/stop.py"
chmod 755 "$BENCH_DIR/stop.py"
echo "  Stopping stale bench/honcho processes..."
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && python3 stop.py"
sudo supervisorctl stop all 2>/dev/null || true
sudo -u "$ERP_USER" bash -c "cd $BENCH_DIR && bench setup supervisor --yes"
sudo cp "$BENCH_DIR/config/supervisor.conf" /etc/supervisor/conf.d/frappe-bench.conf
echo "  [OK] bench supervisor configured"
