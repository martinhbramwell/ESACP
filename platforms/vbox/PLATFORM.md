# Platform: VirtualBox / WSL

The Stage 1 / 1.5 orchestration scripts (`provision.py`, `revertToBaseline.py`,
`chaos/run_scenario.py`) have been deleted — VBox is permanently retired
(2026-03-17 hardware failure) and the pipeline code lives in `tools/pipeline/`.
Only `orchestration/validate_observability.py` (the 27-check harness) remains
and is shared with the KVM platform.

Ansible inventory for this historical platform: `ansible/inventory/dev.yml`

## Environment Variables

```bash
export VM_IP=<VM IP address>
export VM_HOSTNAME=<VirtualBox VM name>
export VM_USER=<SSH username on VM>
export SSH_KEY_PATH=${HOME}/.ssh/<keyname>
export SNAPSHOT_NAME="Stage 1.5 Complete"
```

## Notes

- Host: Windows 11 + WSL2 (Ubuntu)
- `VBoxManage` is discovered automatically in WSL (`/mnt/c/Program Files/Oracle/VirtualBox/`)
  or from PATH on native Linux.
- Bridged networking: VM obtains an IP on the host's LAN via DHCP.
- Stage 1/1.5 are complete and stable on this platform.
