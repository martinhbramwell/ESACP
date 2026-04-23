# 02_build_seed.sh — render cloud-init user-data/meta-data into seed ISO locally.

step "Phase 2: Build hub seed ISO"

SEED_ISO="${SCRIPT_DIR}/${HUB_KEY}-seed.iso"
USER_DATA="${SCRIPT_DIR}/cloud-init/${HUB_KEY}/user-data"
META_DATA="${SCRIPT_DIR}/cloud-init/${HUB_KEY}/meta-data"

[[ -f "${USER_DATA}" ]] || die "Missing: ${USER_DATA}"
[[ -f "${META_DATA}" ]] || die "Missing: ${META_DATA}"

if [[ -f "${SEED_ISO}" \
    && "${SEED_ISO}" -nt "${USER_DATA}" \
    && "${SEED_ISO}" -nt "${META_DATA}" ]]; then
    log "Seed ISO is current — skipping rebuild."
else
    cloud-localds "${SEED_ISO}" "${USER_DATA}" "${META_DATA}"
    log "✅  ${SEED_ISO}"
fi
