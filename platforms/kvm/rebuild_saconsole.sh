#!/usr/bin/env bash
# ============================================================================
# rebuild_saconsole.sh — atomic CLI rebuild of the WireGuard hub.
#
# Issue: #222. Saconsole lifecycle is CLI-only by design.
# Blast radius: saconsole only. hosts_map.yml + SOPS keys + controller WG
# state are NOT touched — they are the source of truth and survive the VM.
#
# Phases:
#   A  backup   — graceful shutdown, pull qcow2 + seed ISO + domain XML to
#                 controller archive, verify with qemu-img info + SHA256.
#   B  teardown — pre-flight guard (no other domain shares saconsole's
#                 volumes), snapshot-delete, virsh destroy (if running),
#                 virsh undefine --remove-all-storage.
#   C  bootstrap — delegate to platforms/kvm/bootstrap_hub.sh (9-phase
#                 idempotent: seed → autoinstall → Fresh Install snap →
#                 Ansible → Stage 2.2 Baseline snap → handoff).
#   D  verify   — clear stale known_hosts, ping hub over WG, SSH via
#                 you@10.10.0.1, assert hub-critical sync_check rows ✅.
#
# PENDING (Phase E, not in this script yet):
#   E-1 (#226) — start observability docker stack on fresh hub.
#   E-2 (#227) — re-register pre-existing WG spokes on fresh hub.
# Until Phase E lands, the rebuilt hub has empty WG peer table + no
# observability containers — sync_check will show ~9 extra failures
# beyond the pre-Run-01 baseline.
#
# Archive: ~/archives/saconsole/  (not in git; keep last 3 generations).
# Transport: libvirt qemu+ssh:// — no sudo on toshy, one TCP stream.
# Perf: ~4 MB/s → ~2.5 h for a 32.5 GiB physical qcow2. See #225.
#
# ---- Manual revert from an archived generation -----------------------------
# 1. ssh toshiba "virsh --connect qemu:///system destroy saconsole" 2>/dev/null || true
# 2. ssh toshiba "virsh --connect qemu:///system undefine --remove-all-storage saconsole" 2>/dev/null || true
# 3. Pick an archive:
#      ARCH=~/archives/saconsole/saconsole-pre-rebuild-YYYY-MM-DD-HHMM
#      sha256sum -c "$ARCH.sha256"
# 4. Restore volumes into pool esacp (over qemu+ssh):
#      virsh -c qemu+ssh://toshiba/system vol-create-as esacp saconsole.qcow2 \
#          "$(stat -c%s "$ARCH.qcow2")" --format qcow2
#      virsh -c qemu+ssh://toshiba/system vol-upload saconsole.qcow2 "$ARCH.qcow2" --pool esacp
#      virsh -c qemu+ssh://toshiba/system vol-create-as esacp saconsole-seed.iso \
#          "$(stat -c%s "$ARCH.seed.iso")" --format raw
#      virsh -c qemu+ssh://toshiba/system vol-upload saconsole-seed.iso "$ARCH.seed.iso" --pool esacp
# 5. Redefine the domain from the archived XML:
#      virsh -c qemu+ssh://toshiba/system define "$ARCH.xml"
# 6. Start it:
#      virsh -c qemu+ssh://toshiba/system start saconsole
# Note: the restored VM has the SAME WG keys + SSH host keys as the original
# archive — pre-existing spokes stay valid without Phase E work.
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
HUB_USER="${ESACP_VM_USER:-you}"               # matches config.sh VM_USER
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

phase_b_teardown() {
  log B "pre-teardown guard: verify no other domain shares saconsole's volumes"

  sac_paths="$($VIRSH domblklist "$HUB_VM_NAME" | awk 'NR>2 && $2 != "-" {print $2}')"
  [ -n "$sac_paths" ] || { log B "ERROR: saconsole has no volumes (unexpected)"; exit 2; }

  log B "saconsole volumes to be removed:"
  printf '    %s\n' $sac_paths

  others="$($VIRSH list --all --name | awk 'NF' | grep -vx "$HUB_VM_NAME" || true)"
  if [ -n "$others" ]; then
    log B "other domains on $SSH_HOST (will NOT be touched):"
    while IFS= read -r dom; do
      [ -z "$dom" ] && continue
      dstate="$($VIRSH domstate "$dom" | tr -d '[:space:]')"
      printf '    %-32s %s\n' "$dom" "$dstate"
    done <<< "$others"
    while IFS= read -r dom; do
      [ -z "$dom" ] && continue
      dom_paths="$($VIRSH domblklist "$dom" | awk 'NR>2 && $2 != "-" {print $2}')"
      for p in $sac_paths; do
        if printf '%s\n' $dom_paths | grep -Fxq "$p"; then
          log B "ERROR: domain '$dom' also references $p — aborting"
          exit 2
        fi
      done
    done <<< "$others"
  fi
  log B "guard passed — only saconsole will be touched"

  state="$($VIRSH domstate "$HUB_VM_NAME" | tr -d '[:space:]')"
  if [ "$state" = "running" ]; then
    log B "saconsole is running — hard stop (virsh destroy)"
    $VIRSH destroy "$HUB_VM_NAME"
  fi

  snaps="$($VIRSH snapshot-list "$HUB_VM_NAME" --name | awk 'NF')"
  if [ -n "$snaps" ]; then
    log B "deleting existing snapshots (preserved in archive qcow2)"
    while IFS= read -r s; do
      [ -z "$s" ] && continue
      log B "  snapshot-delete $s"
      $VIRSH snapshot-delete "$HUB_VM_NAME" "$s"
    done <<< "$snaps"
  fi

  log B "virsh undefine --remove-all-storage $HUB_VM_NAME"
  $VIRSH undefine --remove-all-storage "$HUB_VM_NAME"

  log B "teardown complete"
}

phase_c_bootstrap() {
  log C "delegating to platforms/kvm/bootstrap_hub.sh"
  log C "(expect 30–60 min: seed + autoinstall + ansible + snapshots + handoff)"
  bash "$SCRIPT_DIR/bootstrap_hub.sh"
  log C "bootstrap complete"
}

phase_d_verify() {
  log D "clear stale known_hosts entries for rebuilt hub"
  for h in "$HUB_HOSTNAME" "$HUB_WG_IP" "$HUB_VIRBR0_IP"; do
    ssh-keygen -R "$h" >/dev/null 2>&1 || true
  done

  log D "ping hub ($HUB_WG_IP)"
  ping -c 2 -W 2 "$HUB_WG_IP" >/dev/null \
    || { log D "ERROR: hub ping failed"; exit 2; }
  log D "  ping OK"

  log D "SSH to hub ($HUB_USER@$HUB_WG_IP via WG)"
  ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
      -o BatchMode=yes "$HUB_USER@$HUB_WG_IP" 'true' \
    || { log D "ERROR: SSH to hub failed"; exit 2; }
  log D "  SSH OK"

  log D "sync_check.sh — assert hub-critical ✅ rows"
  tmp="$(mktemp)"
  bash "$SCRIPT_DIR/sync_check.sh" > "$tmp" 2>&1 || true
  required=(
    "MCP grafana"
    "Telegram bot"
    "github MCP entry present"
  )
  for r in "${required[@]}"; do
    if ! grep -q "✅.*$r" "$tmp"; then
      log D "ERROR: sync_check missing ✅ for '$r'"
      grep -n "$r" "$tmp" || true
      rm -f "$tmp"
      exit 2
    fi
  done
  grep -E "Passed:|Warnings:|Failed:" "$tmp" | tail -1
  rm -f "$tmp"
  log D "  sync_check hub-critical rows green"

  log D "verify complete — saconsole rebuild healthy"
}

case "${1:-all}" in
  backup|A)    phase_a_backup ;;
  teardown|B)  phase_b_teardown ;;
  bootstrap|C) phase_c_bootstrap ;;
  verify|D)    phase_d_verify ;;
  all)         phase_a_backup; phase_b_teardown; phase_c_bootstrap; phase_d_verify ;;
  *)           echo "usage: $0 [backup|teardown|bootstrap|verify|all]"; exit 64 ;;
esac
