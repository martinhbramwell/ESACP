#!/usr/bin/env bash
set -euo pipefail
# Section A2e: deploy controller pubkey to erpadm authorized_keys.
# Needs env: ERP_USER
echo "=== A2e: deploy controller pubkey ==="
ERPADM_SSH="/home/$ERP_USER/.ssh"
ERPADM_AK="$ERPADM_SSH/authorized_keys"
if [ ! -f /tmp/hasan_mighty.pub ]; then
    echo "  [WARN] /tmp/hasan_mighty.pub not found — skipped"
    exit 0
fi
mkdir -p "$ERPADM_SSH"
if [ -f "$ERPADM_AK" ] && grep -qf /tmp/hasan_mighty.pub "$ERPADM_AK" 2>/dev/null; then
    echo "  [OK] controller pubkey already in authorized_keys — skipping"
else
    cat /tmp/hasan_mighty.pub >> "$ERPADM_AK"
    echo "  [OK] controller pubkey appended to $ERPADM_AK"
fi
chmod 700 "$ERPADM_SSH"
chmod 600 "$ERPADM_AK"
chown -R "$ERP_USER:$ERP_USER" "$ERPADM_SSH"
rm -f /tmp/hasan_mighty.pub
