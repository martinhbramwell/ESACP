#!/usr/bin/env bash
# create_seeds.sh — Build cloud-init seed ISOs for saconsole and target1
#
# Each seed ISO is mounted as a second CDROM during virt-install.
# The Ubuntu subiquity installer detects the CIDATA volume and reads
# user-data / meta-data to drive an unattended autoinstall.
#
# Usage (from project root):
#   bash platforms/kvm/create_seeds.sh
#
# Prerequisites: cloud-image-utils (cloud-localds)
# Output: platforms/kvm/saconsole-seed.iso, platforms/kvm/target1-seed.iso

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLOUD_INIT_DIR="${SCRIPT_DIR}/cloud-init"

if ! command -v cloud-localds &>/dev/null; then
    echo "ERROR: cloud-localds not found. Run: sudo apt install cloud-image-utils"
    exit 1
fi

for vm in saconsole target1; do
    USER_DATA="${CLOUD_INIT_DIR}/${vm}/user-data"
    META_DATA="${CLOUD_INIT_DIR}/${vm}/meta-data"
    OUTPUT="${SCRIPT_DIR}/${vm}-seed.iso"

    if [[ ! -f "${USER_DATA}" ]]; then
        echo "ERROR: ${USER_DATA} not found."
        exit 1
    fi
    if [[ ! -f "${META_DATA}" ]]; then
        echo "ERROR: ${META_DATA} not found."
        exit 1
    fi

    echo "Building ${vm}-seed.iso..."
    cloud-localds "${OUTPUT}" "${USER_DATA}" "${META_DATA}"
    echo "  ✅  ${OUTPUT}"
done

echo ""
echo "Both seed ISOs ready. Run platforms/kvm/create_vms.sh to create the VMs."
