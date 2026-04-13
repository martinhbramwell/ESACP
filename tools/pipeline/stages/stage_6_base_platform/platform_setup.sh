#!/usr/bin/env bash
set -euo pipefail

# Stage 6a: Base platform setup (sections A, A2, A2b, A2c, A2e, B, C)
# Usage: sudo bash platform_setup.sh BENCH_DIR BENCH_DIR_ORIG ERP_USER

BENCH_DIR="$1"
BENCH_DIR_ORIG="$2"
ERP_USER="$3"

echo "=== A: deploy pre-rendered envars.sh ==="
sudo mkdir -p /opt/ce_sri
sudo cp /tmp/rendered/envars.sh /opt/ce_sri/envars.sh
sudo chmod 644 /opt/ce_sri/envars.sh
echo "  [OK] /opt/ce_sri/envars.sh"

echo "=== A2: symlink bench dir ==="
if sudo test -d "$BENCH_DIR_ORIG" && ! sudo test -L "$BENCH_DIR"; then
    sudo -u "$ERP_USER" ln -sf "$BENCH_DIR_ORIG" "$BENCH_DIR"
    echo "  [OK] symlinked $BENCH_DIR_ORIG -> $BENCH_DIR"
elif sudo test -L "$BENCH_DIR"; then
    echo "  [OK] $BENCH_DIR symlink already exists — skipping"
else
    echo "  [ERROR] Neither $BENCH_DIR_ORIG nor $BENCH_DIR found"
    exit 1
fi

echo "=== A2b: deploy Procfile ==="
PROCFILE="$BENCH_DIR/Procfile"
if ! grep -q 'ce_sri_svc' "$PROCFILE" 2>/dev/null; then
    cp /tmp/rendered/Procfile "$PROCFILE"
    chown "$ERP_USER:$ERP_USER" "$PROCFILE"
    echo "  [OK] Procfile deployed"
else
    echo "  [OK] Procfile already contains ce_sri_svc — skipping"
fi

echo "=== A2c: setup deploy keys for GitHub ==="
mkdir -p "/home/$ERP_USER/.ssh"
chmod 700 "/home/$ERP_USER/.ssh"
for key in you_gh_ce_sri you_gh_ce_sri_svc you_gh_route_planner you_gh.txt; do
    if [ -f "/tmp/$key" ]; then
        mv "/tmp/$key" "/home/$ERP_USER/.ssh/$key"
        chmod 600 "/home/$ERP_USER/.ssh/$key"
    fi
done
cp /tmp/rendered/ssh_config "/home/$ERP_USER/.ssh/config"
chmod 600 "/home/$ERP_USER/.ssh/config"
cp /tmp/rendered/gh_askpass.sh "/home/$ERP_USER/.ssh/gh_askpass.sh"
chmod 700 "/home/$ERP_USER/.ssh/gh_askpass.sh"
chown -R "$ERP_USER:$ERP_USER" "/home/$ERP_USER/.ssh"
echo "  [OK] deploy keys + SSH config installed"

echo "=== A2e: deploy controller pubkey ==="
ERPADM_SSH="/home/$ERP_USER/.ssh"
ERPADM_AK="$ERPADM_SSH/authorized_keys"
if [ -f /tmp/hasan_mighty.pub ]; then
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
else
    echo "  [WARN] /tmp/hasan_mighty.pub not found — skipped"
fi

echo "=== B: fix ownership of BKP ==="
if [ -d "$BENCH_DIR/BKP" ]; then
    sudo chown -R "$ERP_USER:$ERP_USER" "$BENCH_DIR/BKP"
    echo "  [OK] BKP ownership -> $ERP_USER"
else
    echo "  [SKIP] $BENCH_DIR/BKP not found"
fi

echo "=== C: BaRe/envars.sh symlink ==="
if [ -d "$BENCH_DIR/BaRe" ]; then
    sudo -u "$ERP_USER" ln -sf /opt/ce_sri/envars.sh "$BENCH_DIR/BaRe/envars.sh"
    echo "  [OK] BaRe/envars.sh -> /opt/ce_sri/envars.sh"
else
    echo "  [SKIP] $BENCH_DIR/BaRe not yet cloned — will link after clone_and_services.sh"
fi
