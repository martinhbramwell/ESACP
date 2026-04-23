# 05b_wait_cloud_init.sh — block until cloud-init reaches 'done' on hub.
#
# sshd comes up before cloud-init finishes its final modules. In particular,
# /etc/sudoers.d/<admin-user> is written late — roughly 450 ms before
# /var/lib/cloud/instance/boot-finished. Without this wait the snapshot in
# Phase 6 captures a VM where passwordless sudo is not yet configured, AND
# the Ansible fact-gather in Phase 7 races cloud-init and fails with
# "Missing sudo password". See GH #231 for the full timeline evidence.
#
# cloud-init status --wait blocks the SSH session via cloud-init's own IPC
# until it reaches a terminal state ('done' or 'error'). This is not a
# controller-side poll; the target drives the wait.

step "Phase 5b: Wait for cloud-init to reach 'done' on hub"
ssh "${HUB_SSH_OPTS[@]}" "${HUB_USER}@${HUB_VIRBR0_IP}" \
    'cloud-init status --wait' \
    || die "cloud-init did not reach 'done' state on hub"
log "✅  cloud-init done."
