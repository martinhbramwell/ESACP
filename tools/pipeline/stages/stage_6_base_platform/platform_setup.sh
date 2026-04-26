#!/usr/bin/env bash
set -euo pipefail

# Stage 6a (thin orchestrator): pre-clone base-platform sections (A, A2, A2b, A2c, A2e, B)
# Section C (BaRe/envars.sh symlink) runs from clone_and_services.sh after BaRe is cloned.
# Usage: sudo bash platform_setup.sh BENCH_DIR BENCH_DIR_ORIG ERP_USER [PROVISION_MODE]

BENCH_DIR="$1"
BENCH_DIR_ORIG="$2"
ERP_USER="$3"
PROVISION_MODE="${4:-restored}"

bash /tmp/section_a_envars.sh "$PROVISION_MODE"
bash /tmp/section_a2_bench_symlink.sh "$BENCH_DIR" "$BENCH_DIR_ORIG" "$ERP_USER"
bash /tmp/section_a2b_procfile.sh "$BENCH_DIR" "$ERP_USER" "$PROVISION_MODE"
bash /tmp/section_a2c_deploy_keys.sh "$ERP_USER" "$PROVISION_MODE"
bash /tmp/section_a2e_controller_pubkey.sh "$ERP_USER"
bash /tmp/section_b_bkp_owner.sh "$BENCH_DIR" "$ERP_USER"
