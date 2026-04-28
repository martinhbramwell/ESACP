# 02_build_seed.sh — render hub autoinstall artifacts via Jinja2 + hosts_map.yml
# and pack them into a NoCloud seed ISO. Replaces the static cloud-init/<hub>/
# pattern (#202).

step "Phase 2: Build hub seed ISO"

SEED_ISO="${SCRIPT_DIR}/${HUB_KEY}-seed.iso"

PYTHONPATH="${PROJ_ROOT}" \
    "${PROJ_ROOT}/tools/pipeline/orchestration/hub_seed_iso.py" \
    "${HUB_KEY}" "${HUB_VIRBR0_IP}" "${SCRIPT_DIR}" \
    || die "hub seed ISO build failed"

log "✅  ${SEED_ISO}"
