# 07_ansible_provision.sh — run site-kvm.yml limited to the hub, via ProxyJump.

step "Phase 7: Ansible provision hub"
log "ProxyJump : ${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}"
log "Limit     : hub (Play 4 / controller WireGuard is a separate step)"

export ANSIBLE_CONFIG="${ANSIBLE_DIR}/ansible.cfg"
export ANSIBLE_PRIVATE_KEY_FILE="${SSH_KEY}"

# ansible_ssh_common_args adds the ProxyJump to all SSH connections from Ansible.
# It is appended to ssh_args in ansible.cfg — both apply simultaneously.
# --limit ${HUB_KEY} skips Play 3 (target1) and Play 4 (localhost/controller).
cd "${ANSIBLE_DIR}"
ansible-playbook \
    -i inventory/kvm.yml \
    site-kvm.yml \
    --limit ${HUB_KEY} \
    --extra-vars "ansible_ssh_common_args='-J ${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}'"

log "✅  Ansible provision complete."
