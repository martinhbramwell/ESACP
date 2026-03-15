#!/usr/bin/env bash
# destroy_vms.sh — cleanly destroy all three ESACP VBox VMs
#
# Safe sequence per VM:
#   1. Detect state — skip gracefully if VM is not registered
#   2. Force-poweroff if running / paused / saved / stuck
#   3. Poll until VBoxSVC confirms poweroff state (VDI released)
#   4. Unregister (registry only — no --delete)
#   5. Remove VM directory on D:\VM_images (rm -rf, bypasses VBoxSVC)

set -euo pipefail

VBOXMANAGE="VBoxManage.exe"
VM_BASE="/mnt/d/VM_images"
ESACP_VMS=(console target1 target2)
POWEROFF_TIMEOUT=30   # seconds to wait for poweroff confirmation

# ── Helpers ───────────────────────────────────────────────────────────────────

ts() { date '+%H:%M:%S'; }

vm_state() {
    "${VBOXMANAGE}" showvminfo "$1" --machinereadable 2>/dev/null \
        | grep '^VMState=' | cut -d'"' -f2
}

vm_registered() {
    "${VBOXMANAGE}" showvminfo "$1" --machinereadable &>/dev/null
}

# Print all VDI paths attached to a VM (for open-handle diagnostics)
vm_vdi_paths() {
    local vm="$1"
    "${VBOXMANAGE}" showvminfo "${vm}" --machinereadable 2>/dev/null \
        | grep '^"Hard' \
        | sed 's/.*="\(.*\)"/\1/' \
        | grep -v '^$' || true
}

# Check whether any Windows/WSL process has a file in a directory open.
# Uses /proc/*/fd (WSL can see Windows process fds for files on /mnt/).
check_open_handles() {
    local dir="$1"
    local label="$2"
    local hits
    hits=$(find /proc/*/fd -maxdepth 0 -type d 2>/dev/null \
           | xargs -I{} sh -c "ls -la {}/ 2>/dev/null | grep -F '${dir}'" 2>/dev/null \
           | head -5 || true)
    if [[ -n "${hits}" ]]; then
        echo "    [diag] open handles on ${label}:"
        echo "${hits}" | sed 's/^/      /'
    else
        echo "    [diag] no open handles detected on ${label}"
    fi
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
            echo "  ${vm}: discarding saved state..."
            "${VBOXMANAGE}" discardstate "${vm}" 2>&1 | grep -v '^$' || true
            ;;
        running|paused|starting|restoring|snapshotting|livesnapshotting|*)
            echo "  ${vm}: sending poweroff (state=${state})..."
            "${VBOXMANAGE}" controlvm "${vm}" poweroff 2>&1 | grep -v '^$' || true
            ;;
    esac

    # Poll until VBoxSVC confirms poweroff
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
        echo "  ${vm}: not registered — skipping"
        return 0
    fi

    # Diagnostic: show VDI paths and any open handles before unregistering
    local vdis
    vdis=$(vm_vdi_paths "${vm}")
    if [[ -n "${vdis}" ]]; then
        echo "    [diag] ${vm} VDI paths:"
        echo "${vdis}" | sed 's/^/      /'
        while IFS= read -r vdi; do
            local win_path="${vdi}"
            # Convert Windows path to WSL path for fuser check
            local wsl_path
            wsl_path=$(wslpath "${win_path}" 2>/dev/null || true)
            if [[ -n "${wsl_path}" && -f "${wsl_path}" ]]; then
                local fuser_out
                fuser_out=$(fuser "${wsl_path}" 2>/dev/null || true)
                if [[ -n "${fuser_out}" ]]; then
                    echo "    [diag] ⚠️  ${vm} VDI held open by PIDs: ${fuser_out}"
                else
                    echo "    [diag] ${vm} VDI: no fuser hits (file not locked)"
                fi
            else
                echo "    [diag] ${vm} VDI path not reachable via WSL (${wsl_path:-conversion failed})"
            fi
        done <<< "${vdis}"
    else
        echo "    [diag] ${vm}: no VDI paths found in showvminfo"
    fi

    echo "  [$(ts)] ${vm}: calling unregistervm..."
    "${VBOXMANAGE}" unregistervm "${vm}" 2>&1 | grep -v '^$' || true
    echo "  [$(ts)] ${vm}: ✅  unregistervm returned"

    # Diagnostic: confirm VM is gone from registry
    if vm_registered "${vm}"; then
        echo "    [diag] ⚠️  ${vm} still appears in VBoxManage list vms after unregister!"
    else
        echo "    [diag] ${vm} confirmed absent from registry"
    fi
}

cleanup_dir() {
    local vm="$1"
    local dir="${VM_BASE}/${vm}"
    if [[ ! -d "${dir}" ]]; then
        echo "  ${vm}: directory already gone"
        return 0
    fi

    # Diagnostic: check for open handles before rm -rf
    check_open_handles "${dir}" "${vm}"

    echo "  [$(ts)] ${vm}: rm -rf ${dir}..."
    rm -rf "${dir}"
    echo "  [$(ts)] ${vm}: ✅  directory removed"
}

# ── Main ──────────────────────────────────────────────────────────────────────

echo ""
echo "ESACP VBox — Destroy All VMs"
echo "════════════════════════════"
echo ""

# Diagnostic: show VBoxSVC and VBoxHeadless processes at start
echo "── Diagnostic: VBox processes at start ─────────────"
tasklist.exe 2>/dev/null | grep -iE 'VBoxSVC|VBoxHeadless' | sed 's/^/  /' || true
echo ""

# Phase 1: poweroff all VMs
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

# Diagnostic: show VBox processes after poweroff, before unregister
echo ""
echo "── Diagnostic: VBox processes after poweroff ───────"
tasklist.exe 2>/dev/null | grep -iE 'VBoxSVC|VBoxHeadless' | sed 's/^/  /' || echo "  (none)"
echo ""

echo "── Phase 2: Unregister (registry only — files deleted in Phase 3) ──"
for vm in "${ESACP_VMS[@]}"; do
    unregister_vm "${vm}"
    echo ""
done

# Diagnostic: show VBox processes after all unregisters
echo "── Diagnostic: VBox processes after unregister ─────"
tasklist.exe 2>/dev/null | grep -iE 'VBoxSVC|VBoxHeadless' | sed 's/^/  /' || echo "  (none)"
echo ""

echo "── Phase 3: Remove directories ─────────────────────"
for vm in "${ESACP_VMS[@]}"; do
    cleanup_dir "${vm}"
done

echo ""
echo "✅  All ESACP VMs destroyed."
echo ""
