# 04_create_vm.sh — virt-install the hub VM on the hypervisor; idempotent.

step "Phase 4: Create hub VM on ${HYPERVISOR_ALIAS}"

REMOTE_ISO="${REMOTE_IMAGES_DIR}/${UBUNTU_ISO_NAME}"

if vm_exists; then
    log "VM '${HUB_VM_NAME}' already exists on ${HYPERVISOR_ALIAS} — skipping creation."
else
    remote "test -f '${REMOTE_ISO}'" \
        || die "Ubuntu ISO not found on ${HYPERVISOR_ALIAS}: ${REMOTE_ISO}"

    log "Running virt-install on ${HYPERVISOR_ALIAS} (autoinstall will run headlessly) ..."

    # Run via SSH heredoc to avoid shell quoting issues with multi-argument commands.
    # Variables are expanded locally before being sent to the remote shell.
    #
    # --os-variant ubuntu20.04: toshiba's osinfo-db (Ubuntu 20.04 stock) tops out at
    #   ubuntu20.04 — ubuntu22.04 and ubuntu24.04 are both absent.
    # --disk pool=esacp: stores ${HUB_VM_NAME}.qcow2 in the esacp pool
    #   (/mnt/esacp-disk/var/lib/libvirt/images) — system disk is 98% full.
    # --noautoconsole: returns immediately; autoinstall runs headlessly.
    ssh "${HYPERVISOR_USER}@${HYPERVISOR_ALIAS}" bash <<REMOTE
virt-install \
    --connect qemu:///system \
    --name ${HUB_VM_NAME} \
    --ram 4096 \
    --vcpus 2 \
    --disk pool=esacp,size=20,format=qcow2 \
    --location "${REMOTE_ISO},kernel=casper/vmlinuz,initrd=casper/initrd" \
    --disk "path=${REMOTE_SEED},device=cdrom,readonly=on" \
    --network network=default \
    --os-variant ubuntu20.04 \
    --extra-args 'autoinstall ds=nocloud' \
    --graphics vnc \
    --noautoconsole
REMOTE

    log "✅  VM created and autoinstall running."
fi
