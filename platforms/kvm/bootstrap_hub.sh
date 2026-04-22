#!/usr/bin/env bash
# bootstrap_hub.sh — Idempotent bootstrap of the hub VM on a remote KVM hypervisor.
#
# Thin orchestrator. Phase implementations live in platforms/kvm/bootstrap_hub/:
#   01_preflight           04_create_vm          07_ansible_provision
#   02_build_seed          05_wait_ssh           08_snapshot_baseline
#   03_upload_seed         05b_wait_cloud_init   09_handoff
#                          06_snapshot_fresh     99_summary
#
# Usage (from project root):
#   bash platforms/kvm/bootstrap_hub.sh
#
# Prerequisites:
#   - cloud-image-utils (cloud-localds) installed on this controller
#   - SSH alias for hypervisor configured in ~/.ssh/config (see config.sh)
#   - SSH keypair for KVM VM guests (path from config.sh / ESACP_SSH_KEY)
#   - SOPS age key at ~/.config/sops/age/keys.txt (for Ansible secrets)
#
# Idempotency: safe to re-run at any phase. Each phase checks current state
# before acting. Delete hub VM + seed ISO to start from scratch.
#
# Decomposed from a 425-line monolith per issue #220.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHASES_DIR="${SCRIPT_DIR}/bootstrap_hub"

# Configuration from hosts_map.yml + env overrides.
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

# Phase-shared constants.
UBUNTU_ISO_NAME="ubuntu-24.04.4-live-server-amd64.iso"
SNAPSHOT_FRESH="Fresh Install"
SNAPSHOT_BASELINE="Stage 2.2 Baseline"
AUTOINSTALL_TIMEOUT=1800   # 30 minutes — max wait for autoinstall to complete
SSH_POLL_TIMEOUT=120       # 2 minutes  — max wait for SSH after first boot

# shellcheck source=bootstrap_hub/_helpers.sh
source "${PHASES_DIR}/_helpers.sh"

# Phase dispatch — each file is imperative and uses helpers/env from above.
# shellcheck source=bootstrap_hub/01_preflight.sh
source "${PHASES_DIR}/01_preflight.sh"
# shellcheck source=bootstrap_hub/02_build_seed.sh
source "${PHASES_DIR}/02_build_seed.sh"
# shellcheck source=bootstrap_hub/03_upload_seed.sh
source "${PHASES_DIR}/03_upload_seed.sh"
# shellcheck source=bootstrap_hub/04_create_vm.sh
source "${PHASES_DIR}/04_create_vm.sh"
# shellcheck source=bootstrap_hub/05_wait_ssh.sh
source "${PHASES_DIR}/05_wait_ssh.sh"
# shellcheck source=bootstrap_hub/05b_wait_cloud_init.sh
source "${PHASES_DIR}/05b_wait_cloud_init.sh"
# shellcheck source=bootstrap_hub/06_snapshot_fresh.sh
source "${PHASES_DIR}/06_snapshot_fresh.sh"
# shellcheck source=bootstrap_hub/07_ansible_provision.sh
source "${PHASES_DIR}/07_ansible_provision.sh"
# shellcheck source=bootstrap_hub/08_snapshot_baseline.sh
source "${PHASES_DIR}/08_snapshot_baseline.sh"
# shellcheck source=bootstrap_hub/09_handoff.sh
source "${PHASES_DIR}/09_handoff.sh"
# shellcheck source=bootstrap_hub/99_summary.sh
source "${PHASES_DIR}/99_summary.sh"
