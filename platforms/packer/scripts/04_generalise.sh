#!/usr/bin/env bash
# 04_generalise.sh — Generalise the image before export
#
# Runs INSIDE the build VM as root (via: sudo env ERP_USER=... bash {{ .Path }})
# Strips machine-specific identity so every VM deployed from this image
# gets a fresh identity on first boot.
#
# Mirrors the "generalisation" step in cloud image preparation:
#   - Remove SSH host keys (regenerated on first boot by openssh-server)
#   - Clear machine-id (regenerated on first boot by systemd)
#   - Truncate apt caches (reduces image size)
#   - Remove bash history

set -euo pipefail

# ERP_USER is passed by Packer execute_command — not hardcoded here.
ERP_USER="${ERP_USER:?ERP_USER env var not set — pass via Packer execute_command}"

log() { echo "[04_generalise $(date '+%H:%M:%S')] $*"; }

# ── SSH host keys ──────────────────────────────────────────────────────────────
log "Removing SSH host keys ..."
rm -f /etc/ssh/ssh_host_*

# ── machine-id ────────────────────────────────────────────────────────────────
log "Clearing machine-id ..."
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id
ln -s /etc/machine-id /var/lib/dbus/machine-id

# ── apt cache ─────────────────────────────────────────────────────────────────
log "Cleaning apt cache ..."
apt-get clean
rm -rf /var/lib/apt/lists/*

# ── bash history ──────────────────────────────────────────────────────────────
log "Clearing bash histories ..."
rm -f /root/.bash_history
rm -f /home/you/.bash_history
rm -f "/home/${ERP_USER}/.bash_history"

# ── cloud-init ────────────────────────────────────────────────────────────────
# Reset cloud-init state so it runs again on first boot of the deployed VM.
log "Resetting cloud-init ..."
cloud-init clean --logs 2>/dev/null || true

log "✓  Image generalised — ready for export"
