#!/usr/bin/env bash
set -euo pipefail

# Stage 6b (thin orchestrator): clone apps + services + BaRe envars symlink
# Sections: A2d (ce_sri family + BaRe), A3+A3b (supervisor), B2b (npm), C (BaRe symlink)
# Usage: sudo bash clone_and_services.sh BENCH_DIR ERP_USER [PROVISION_MODE]

BENCH_DIR="$1"
ERP_USER="$2"
PROVISION_MODE="${3:-restored}"

bash /tmp/section_a2d_clone_cesri.sh "$BENCH_DIR" "$ERP_USER" "$PROVISION_MODE"
bash /tmp/section_a2d_clone_bare.sh "$BENCH_DIR" "$ERP_USER"
bash /tmp/section_a3_supervisor.sh "$BENCH_DIR" "$ERP_USER" "$PROVISION_MODE"
bash /tmp/section_b2b_cesri_npm.sh "$BENCH_DIR" "$ERP_USER" "$PROVISION_MODE"
bash /tmp/section_c_bare_symlink.sh "$BENCH_DIR" "$ERP_USER" "$PROVISION_MODE"
