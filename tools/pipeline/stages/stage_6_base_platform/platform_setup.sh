#!/usr/bin/env bash
set -euo pipefail

# Stage 6a orchestrator — dispatches sections A–C.
# Usage: sudo bash platform_setup.sh BENCH_DIR BENCH_DIR_ORIG ERP_USER MODE
#   MODE = generic | restored (default: restored)
# Sections live in ./sections/ (rsynced to same dir by stage_6_base_platform/__init__.py).

export BENCH_DIR="$1"
export BENCH_DIR_ORIG="$2"
export ERP_USER="$3"
export MODE="${4:-restored}"

if [ "$MODE" = "generic" ]; then
    export ENVARS_DIR="/opt/generic"
else
    export ENVARS_DIR="/opt/ce_sri"
fi
export ENVARS_PATH="${ENVARS_DIR}/envars.sh"

SECTIONS="$(dirname "$0")/sections"

bash "$SECTIONS/ps_a_envars.sh"
bash "$SECTIONS/ps_a2_bench_symlink.sh"
if [ "$MODE" = "generic" ]; then
    echo "=== A2b/A2c: [SKIP] Procfile patch + ce_sri deploy keys (generic) ==="
else
    bash "$SECTIONS/ps_a2b_procfile.sh"
    bash "$SECTIONS/ps_a2c_deploy_keys.sh"
fi
bash "$SECTIONS/ps_a2e_ctrl_pubkey.sh"
bash "$SECTIONS/ps_b_bkp_ownership.sh"
bash "$SECTIONS/ps_c_bare_symlink.sh"
