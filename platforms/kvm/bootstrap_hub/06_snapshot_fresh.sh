# 06_snapshot_fresh.sh — snapshot the hub immediately after cloud-init.

step "Phase 6: Snapshot '${SNAPSHOT_FRESH}'"
take_snapshot "${SNAPSHOT_FRESH}"
