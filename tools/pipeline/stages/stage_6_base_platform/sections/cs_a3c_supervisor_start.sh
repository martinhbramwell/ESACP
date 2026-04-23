#!/usr/bin/env bash
set -euo pipefail
# Section A3 (start): reread supervisor, update, start all. Wait for Redis.
# Unchanged across modes. Runs AFTER A3b (which only deploys in restore mode).
# Needs env: ERP_USER
echo "=== A3 (start): supervisor reread/update/start ==="
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all || true
echo "  Waiting 20s for Redis to be ready..."
sleep 20
echo "  [OK] bench services started"
sudo chmod o+x "/home/$ERP_USER"
echo "  [OK] /home/$ERP_USER world-traversable for nginx"
