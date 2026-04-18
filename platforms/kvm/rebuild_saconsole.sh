#!/usr/bin/env bash
# ============================================================================
# rebuild_saconsole.sh — atomic CLI rebuild of the WireGuard hub.
#
# Issue: #222. Saconsole lifecycle is CLI-only by design.
# Blast radius: saconsole only. hosts_map.yml + SOPS keys + controller WG
# state are NOT touched — they are the source of truth and survive the VM.
#
# Phases:  A=backup  B=teardown  C=bootstrap  D=verify
#          (B/C/D added in subsequent commits — Phase A lands first.)
#
# Archive: ~/archives/saconsole/  (not in git; keep last 3 generations)
#
# ---- Manual revert from an archived generation -----------------------------
# (documented in full when Phases B/C/D land.)
# ----------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARCHIVE_DIR="${SACONSOLE_ARCHIVE_DIR:-$HOME/archives/saconsole}"
TS="$(date +%Y-%m-%d-%H%M)"
ARCH_BASE="$ARCHIVE_DIR/saconsole-pre-rebuild-$TS"

# Identity — resolved from hosts_map.yml (no hardcoded names).
cd "$PROJECT_ROOT"
eval "$("$PROJECT_ROOT/tools/host_identity.py")"
: "${HUB_VM_NAME:?hosts_map.yml resolution failed}"
: "${HUB_HYPERVISOR:?hosts_map.yml resolution failed}"

SSH_HOST="${SACONSOLE_SSH_HOST:-$HUB_HYPERVISOR}"
POOL="${SACONSOLE_POOL:-esacp}"
VIRSH="virsh -c qemu+ssh://$SSH_HOST/system"   # libvirt-native remote transport

log() { printf '[rebuild:%s] %s\n' "$1" "$2"; }

phase_a_backup() {
  log A "archive dir: $ARCHIVE_DIR"
  mkdir -p "$ARCHIVE_DIR"

  log A "dump persistent domain XML (pre-shutdown)"
  $VIRSH dumpxml --inactive "$HUB_VM_NAME" > "$ARCH_BASE.xml"
  [ -s "$ARCH_BASE.xml" ] || { log A "ERROR: domain XML empty"; exit 2; }

  log A "graceful shutdown of $HUB_VM_NAME via $SSH_HOST"
  $VIRSH shutdown "$HUB_VM_NAME" || true

  state=""
  for _ in $(seq 1 60); do
    state="$($VIRSH domstate "$HUB_VM_NAME" | tr -d '[:space:]')"
    [ "$state" = "shutoff" ] && break
    sleep 2
  done
  [ "$state" = "shutoff" ] || { log A "ERROR: not shut off in 120s (state=$state)"; exit 2; }
  log A "shutdown confirmed"

  log A "vol-download $HUB_VM_NAME.qcow2 → $ARCH_BASE.qcow2"
  $VIRSH vol-download "$HUB_VM_NAME.qcow2" --pool "$POOL" "$ARCH_BASE.qcow2"

  log A "vol-download $HUB_VM_NAME-seed.iso → $ARCH_BASE.seed.iso"
  $VIRSH vol-download "$HUB_VM_NAME-seed.iso" --pool "$POOL" "$ARCH_BASE.seed.iso"

  log A "verify qcow2 integrity"
  qemu-img info "$ARCH_BASE.qcow2" >/dev/null

  (cd "$ARCHIVE_DIR" && sha256sum \
      "$(basename "$ARCH_BASE").xml" \
      "$(basename "$ARCH_BASE").qcow2" \
      "$(basename "$ARCH_BASE").seed.iso") | tee "$ARCH_BASE.sha256"

  log A "backup complete: $ARCH_BASE.{xml,qcow2,seed.iso}"
}

case "${1:-all}" in
  backup|A) phase_a_backup ;;
  all)      phase_a_backup ;;   # B/C/D added in later commits
  *)        echo "usage: $0 [backup|all]"; exit 64 ;;
esac
