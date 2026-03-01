# Platform: VirtualBox / WSL

Existing scripts for this platform live in `orchestration/`:

| Script | Purpose |
|---|---|
| `orchestration/provision.py` | Full provisioning orchestrator |
| `orchestration/revertToBaseline.py` | Snapshot revert via VBoxManage |
| `orchestration/chaos/run_scenario.py` | Chaos failure injection |

Ansible inventory: `ansible/inventory/dev.yml`

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
