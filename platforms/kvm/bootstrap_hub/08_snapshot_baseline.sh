# 08_snapshot_baseline.sh — snapshot the provisioned hub as the Stage 2.2 baseline.

step "Phase 8: Snapshot '${SNAPSHOT_BASELINE}'"
take_snapshot "${SNAPSHOT_BASELINE}"
