#!/usr/bin/env bash
# take_snapshots.sh — Take a named snapshot on all 3 VirtualBox VMs.
#
# Usage (from project root):
#   bash platforms/vbox/take_snapshots.sh "Stage 1.5 Baseline"
#
# The snapshot name defaults to "Stage 1.5 Baseline" if omitted.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

SNAPSHOT_NAME="${1:-Stage 1.5 Baseline}"

find_vboxmanage() {
    for candidate in "VBoxManage" "VBoxManage.exe"; do
        command -v "${candidate}" &>/dev/null && echo "${candidate}" && return
    done
    local p="/mnt/c/Program Files/Oracle/VirtualBox/VBoxManage.exe"
    [[ -f "${p}" ]] && echo "${p}" && return
    echo ""
}

VBM="$(find_vboxmanage)"
[[ -z "${VBM}" ]] && echo "ERROR: VBoxManage not found." && exit 1

for vm in console target1 target2; do
    echo "  Snapshotting ${vm} → \"${SNAPSHOT_NAME}\"..."
    "${VBM}" snapshot "${vm}" take "${SNAPSHOT_NAME}" --description "Taken by take_snapshots.sh"
    echo "  ✅  ${vm} done."
done

echo ""
echo "  ✅  All 3 VMs snapshotted: \"${SNAPSHOT_NAME}\""
