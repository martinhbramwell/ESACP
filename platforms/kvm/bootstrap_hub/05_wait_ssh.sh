# 05_wait_ssh.sh — wait for autoinstall to complete and SSH to come up.

step "Phase 5: Wait for hub to be ready"

if ssh_ready; then
    log "SSH already available — VM is fully up."
else
    # The VM may be:
    #   a) running (autoinstall in progress — will power off when done), or
    #   b) shut off (autoinstall complete — needs to be started), or
    #   c) running (booting up after first shutdown — SSH not yet available)
    DEADLINE=$(( SECONDS + AUTOINSTALL_TIMEOUT ))
    while :; do
        STATE=$(vm_state)
        case "${STATE}" in
            "shut off")
                log "VM shut off — autoinstall complete. Starting hub ..."
                remote virsh --connect qemu:///system start ${HUB_VM_NAME}
                sleep 5
                break
                ;;
            running)
                # Could be mid-autoinstall OR post-reboot boot. Check SSH.
                if ssh_ready; then
                    log "SSH available."
                    break
                fi
                if [[ ${SECONDS} -ge ${DEADLINE} ]]; then
                    die "Autoinstall timed out after ${AUTOINSTALL_TIMEOUT}s."$'\n'"  Debug: ssh ${HYPERVISOR_ALIAS} 'virt-viewer ${HUB_VM_NAME}'"
                fi
                log "  VM running (autoinstall in progress) — waiting 30s ..."
                sleep 30
                ;;
            *)
                log "  VM state: '${STATE}' — waiting 10s ..."
                sleep 10
                ;;
        esac
    done

    # Poll until SSH responds (VM may still be booting after start).
    log "Polling SSH on ${HUB_VIRBR0_IP} via ${HYPERVISOR_ALIAS} ..."
    SSH_DEADLINE=$(( SECONDS + SSH_POLL_TIMEOUT ))
    until ssh_ready; do
        if [[ ${SECONDS} -ge ${SSH_DEADLINE} ]]; then
            die "SSH not ready after ${SSH_POLL_TIMEOUT}s."$'\n'"  Try: ssh -J ${HYPERVISOR_ALIAS} -i ${SSH_KEY} ${HUB_USER}@${HUB_VIRBR0_IP}"
        fi
        log "  Waiting for SSH ..."
        sleep 5
    done
fi

log "✅  SSH ready."
