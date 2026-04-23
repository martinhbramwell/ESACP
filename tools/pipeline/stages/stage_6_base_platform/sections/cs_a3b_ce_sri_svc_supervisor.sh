#!/usr/bin/env bash
set -euo pipefail
# Section A3b: deploy ce_sri_svc supervisor conf. Restore-mode only.
echo "=== A3b: deploy ce_sri_svc supervisor conf ==="
sudo cp /tmp/rendered/ce_sri_svc_supervisor.conf /etc/supervisor/conf.d/ce-sri-svc.conf
echo "  [OK] /etc/supervisor/conf.d/ce-sri-svc.conf deployed"
