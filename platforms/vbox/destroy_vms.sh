#!/usr/bin/env bash
# destroy_vms.sh — cleanly destroy all three ESACP VBox VMs
#
# Safe sequence per VM:
#   1. Detect state — skip gracefully if VM is not registered
#   2. Force-poweroff if running / paused / saved / stuck
#   3. Poll until VBoxSVC confirms poweroff state (VDI released)
#   4. Unregister + delete storage
#   5. Remove any residual directory on D:\VM_images

set -euo pipefail

VBOXMANAGE="VBoxManage.exe"
VM_BASE="/mnt/d/VM_images"
ESACP_VMS=(console target1 target2)
POWEROFF_TIMEOUT=30   # seconds to wait for poweroff confirmation

# ── Helpers ───────────────────────────────────────────────────────────────────

vm_state() {
    "${VBOXMANAGE}" showvminfo "$1" --machinereadable 2>/dev/null \
        | grep '^VMState=' | cut -d'"' -f2
}

vm_registered() {
    "${VBOXMANAGE}" showvminfo "$1" --machinereadable &>/dev/null
}

poweroff_vm() {
    local vm="$1"
    local state
    state=$(vm_state "${vm}" 2>/dev/null || echo "not_found")

    case "${state}" in
        poweroff|aborted)
            echo "  ${vm}: already stopped (${state})"
            return 0
            ;;
        not_found)
            echo "  ${vm}: not registered — nothing to do"
            return 0
            ;;
        saved)
            # discard saved state first, then it becomes poweroff
            echo "  ${vm}: discarding saved state..."
            "${VBOXMANAGE}" discardstate "${vm}" 2>&1 | grep -v '^$' || true
            ;;
        running|paused|starting|restoring|snapshotting|livesnapshotting|*)
            echo "  ${vm}: sending poweroff (state=${state})..."
            "${VBOXMANAGE}" controlvm "${vm}" poweroff 2>&1 | grep -v '^$' || true
            ;;
    esac

    # Poll until VBoxSVC confirms poweroff (VDI file handles are released)
    local elapsed=0
    while true; do
        state=$(vm_state "${vm}" 2>/dev/null || echo "not_found")
        if [[ "${state}" == "poweroff" || "${state}" == "aborted" || "${state}" == "not_found" ]]; then
            echo "  ${vm}: confirmed stopped (${state})"
            return 0
        fi
        if [[ ${elapsed} -ge ${POWEROFF_TIMEOUT} ]]; then
            echo "  ⚠️  ${vm}: did not reach poweroff within ${POWEROFF_TIMEOUT}s (state=${state})"
            echo "       Run from PowerShell (admin): taskkill /F /IM VBoxHeadless.exe /T"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
}

unregister_vm() {
    local vm="$1"
    if ! vm_registered "${vm}"; then
        echo "  ${vm}: not registered — skipping unregister"
        return 0
    fi
    # Do NOT use --delete here: --delete triggers async VBoxSVC storage cleanup
    # that holds a registry lock; the next unregistervm starts during that window
    # and hangs.  File deletion is handled by cleanup_dir (rm -rf) in Phase 3.
    echo "  ${vm}: unregistering (registry only)..."
    "${VBOXMANAGE}" unregistervm "${vm}" 2>&1 | grep -v '^$' || true
    echo "  ${vm}: ✅  unregistered"
}

cleanup_dir() {
    local vm="$1"
    local dir="${VM_BASE}/${vm}"
    if [[ -d "${dir}" ]]; then
        echo "  ${vm}: removing residual directory ${dir}..."
        rm -rf "${dir}"
        echo "  ${vm}: ✅  directory removed"
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────────

echo ""
echo "ESACP VBox — Destroy All VMs"
echo "════════════════════════════"
echo ""

# Phase 1: poweroff all VMs first (parallel where possible)
echo "── Phase 1: Power off ──────────────────────────────"
failed_poweroff=()
for vm in "${ESACP_VMS[@]}"; do
    if ! poweroff_vm "${vm}"; then
        failed_poweroff+=("${vm}")
    fi
done

if [[ ${#failed_poweroff[@]} -gt 0 ]]; then
    echo ""
    echo "❌  Could not power off: ${failed_poweroff[*]}"
    echo "   Kill VBoxHeadless from PowerShell (admin) then re-run:"
    echo "     taskkill /F /IM VBoxHeadless.exe /T"
    echo "     taskkill /F /IM VBoxSVC.exe /T"
    exit 1
fi

# Brief pause to ensure VBoxSVC flushes all file handles before unregister
sleep 3

echo ""
echo "── Phase 2: Unregister (registry only — files deleted in Phase 3) ──"
for vm in "${ESACP_VMS[@]}"; do
    unregister_vm "${vm}"
    sleep 3   # let VBoxSVC settle between registry writes
done

echo ""
echo "── Phase 3: Remove residual directories ────────────"
for vm in "${ESACP_VMS[@]}"; do
    cleanup_dir "${vm}"
done

echo ""
echo "✅  All ESACP VMs destroyed."
echo ""
