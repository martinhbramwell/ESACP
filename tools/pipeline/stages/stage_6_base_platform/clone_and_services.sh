#!/usr/bin/env bash
set -euo pipefail

# Stage 6b orchestrator — dispatches sections A2d, A3, A3b, B2b.
# Usage: sudo bash clone_and_services.sh BENCH_DIR ERP_USER MODE
#   MODE = generic | restored (default: restored)
# Sections live in ./sections/ (rsynced to same dir by stage_6_base_platform/__init__.py).

export BENCH_DIR="$1"
export ERP_USER="$2"
export MODE="${3:-restored}"

if [ "$MODE" = "generic" ]; then
    export ENVARS_PATH="/opt/generic/envars.sh"
else
    export ENVARS_PATH="/opt/ce_sri/envars.sh"
fi

SECTIONS="$(dirname "$0")/sections"

if [ "$MODE" != "generic" ]; then
    bash "$SECTIONS/cs_a2d_bespoke_clones.sh"
else
    echo "=== A2d (bespoke): [SKIP] ce_sri/route_planner/returnable/ce_sri_svc (generic) ==="
fi
bash "$SECTIONS/cs_a2d_bare_clone.sh"

bash "$SECTIONS/cs_a3a_bench_supervisor.sh"
if [ "$MODE" != "generic" ]; then
    bash "$SECTIONS/cs_a3b_ce_sri_svc_supervisor.sh"
else
    echo "=== A3b: [SKIP] ce_sri_svc supervisor conf (generic) ==="
fi
bash "$SECTIONS/cs_a3c_supervisor_start.sh"

if [ "$MODE" != "generic" ]; then
    bash "$SECTIONS/cs_b2b_npm_install.sh"
else
    echo "=== B2b: [SKIP] npm install for ce_sri_svc (generic) ==="
fi

# Re-run section C now that BaRe is cloned — symlink was skipped earlier.
bash "$SECTIONS/ps_c_bare_symlink.sh"
