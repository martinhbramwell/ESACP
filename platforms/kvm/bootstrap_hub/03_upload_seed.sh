# 03_upload_seed.sh — upload seed ISO to hypervisor, skipping if remote is newer.
# Exports REMOTE_SEED for phase 04.

step "Phase 3: Upload seed ISO to ${HYPERVISOR_ALIAS}"

REMOTE_SEED="${REMOTE_IMAGES_DIR}/${HUB_KEY}-seed.iso"
LOCAL_MTIME=$(stat -c %Y "${SEED_ISO}")
REMOTE_MTIME=$(remote "stat -c %Y '${REMOTE_SEED}' 2>/dev/null || echo 0")

if [[ "${REMOTE_MTIME}" -ge "${LOCAL_MTIME}" ]]; then
    log "Remote seed ISO is current — skipping upload."
else
    log "Uploading to ${HYPERVISOR_ALIAS}:${REMOTE_SEED} ..."
    scp "${SEED_ISO}" "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}:${REMOTE_SEED}"
    log "✅  Uploaded."
fi
