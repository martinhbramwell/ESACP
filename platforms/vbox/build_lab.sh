#!/usr/bin/env bash
# build_lab.sh — Full VirtualBox lab bootstrap (WSL side, Phase 1 of 2).
#
# Chains the three WSL-side scripts in order:
#   1. create_vms.sh      — import OVAs, detect IP, wait for SSH
#   2. handoff_console.sh — WireGuard on all VMs, clone repo, WSL spoke up
#
# Phase 2 runs from saconsole:
#   bash /opt/esacp/platforms/vbox/provision_targets.sh
#
# You can also run the steps individually:
#   bash platforms/vbox/create_vms.sh
#   bash platforms/vbox/handoff_console.sh
#
# Prerequisites:
#   - esacp-base.ova at D:\VM_images\
#   - SOPS age key at ~/.config/sops/age/keys.txt
#   - sshpass installed (apt install sshpass)
#
# Usage (from project root):
#   bash platforms/vbox/build_lab.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

bash platforms/vbox/create_vms.sh
bash platforms/vbox/handoff_console.sh
