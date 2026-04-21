# ESACP — KVM Lab Build-Out Procedure

Stage 2.1 — saconsole + target1 from scratch

> **Audience**: operator re-building the lab without external assistance.
> All commands run on the Xubuntu controller host unless stated otherwise.
> Working directory is the project root unless stated otherwise.

---

## 0. Prerequisites

Confirm all host software is present:

```bash
for tool in virsh virt-install cloud-localds ansible ansible-playbook sops age python3; do
    command -v $tool && echo "$tool OK" || echo "$tool MISSING"
done
```

Required packages if anything is missing:

```bash
sudo apt install -y \
    qemu-kvm libvirt-daemon-system virtinst \
    cloud-image-utils wireguard wireguard-tools \
    ansible python3-rich python3-yaml
```

SOPS/age binaries must be at `/usr/local/bin/sops` and `/usr/local/bin/age`.
The age decryption key must be at `~/.config/sops/age/keys.txt`.

Confirm the age key matches the project's `.sops.yaml`:

```bash
age-keygen -y ~/.config/sops/age/keys.txt   # prints public key
grep recipient .sops.yaml                   # must match
```

### Claude Code Cloudflare MCP helper

`Cld.sh` (the project launcher) calls `cf-mcp-refresh` before `claude --chrome`
to keep the Cloudflare MCP OAuth access token fresh. Install the canonical
repo copy onto the operator's `PATH`:

```bash
install -m 0755 tools/cf-mcp-refresh ~/.local/bin/cf-mcp-refresh
```

Re-run the install whenever `tools/cf-mcp-refresh` is updated. `sync_check.sh`
expects the script at `~/.local/bin/cf-mcp-refresh`.

---

## 1. Verify WireGuard Keys

Keys are stored encrypted in `config/wireguard/keys.sops.yml`.
Confirm they decrypt successfully:

```bash
sops -d config/wireguard/keys.sops.yml | grep -c 'private_key'
# expect: 3  (mighty, saconsole, target1)
```

If the file is missing or corrupt, regenerate keys:

```bash
bash config/wireguard/generate_keys.sh
# Follow prompts — outputs keys.sops.yml (encrypted, committed)
# Prints public keys — paste into ansible/group_vars/all.yml
```

---

## 2. Clear Stale SSH Known-Hosts (rebuild only)

If re-building VMs that previously existed, remove the old host keys:

```bash
ssh-keygen -R saconsole
ssh-keygen -R target1
ssh-keygen -R 192.168.122.10
ssh-keygen -R 192.168.122.11
```

---

## 3. Build Cloud-Init Seed ISOs

```bash
bash platforms/kvm/create_seeds.sh
```

Expected output:
```
Building saconsole-seed.iso...  ✅
Building target1-seed.iso...    ✅
```

---

## 4. Create VMs and Start Autoinstall

```bash
bash platforms/kvm/create_vms.sh both
```

This creates both VMs and immediately starts the Ubuntu autoinstall.
The command returns promptly — autoinstall continues in the background.

Optionally monitor progress:

```bash
virt-viewer saconsole &
virt-viewer target1 &
```

---

## 5. Provision Both VMs

Run the provisioner — the pipeline detects mid-autoinstall automatically:

```bash
./tools/esacp.py provision <hostname>
```

(Or drag-to-provision from the Cytoscape control plane.)

The provisioner handles the full lifecycle for each VM in sequence:

| Phase | What happens |
|---|---|
| Auto-detect | If VM is running with no SSH → waits for autoinstall to power off (~10–20 min) |
| Start | Starts the powered-off VM |
| SSH poll | Waits for SSH to become available (~30s from normal boot) |
| Fresh Install snapshot | Captures state before Ansible |
| Ansible | Runs `site-kvm.yml` — all roles for that VM |
| Stage 2.1 Baseline snapshot | Captures fully configured state |

At the end, the provisioner prompts:

```
ℹ️  Your sudo password is required to configure WireGuard on this host.
BECOME password:
```

Enter your sudo password. This configures the **controller WireGuard spoke** (wg0 on this host).

**Total duration**: approximately 45–60 minutes for both VMs combined.

---

## 6. Verify WireGuard Connectivity

After the provisioner completes:

```bash
# Controller → saconsole hub
ping -c 3 10.10.0.1

# Controller → target1 (via saconsole hub routing)
ping -c 3 10.10.0.3

# Peers on saconsole hub
ssh -i ~/.ssh/hasan_mighty you@saconsole "sudo wg show"
# Expect: 2 peers (mighty + target1), recent handshakes
```

---

## 7. Run Validation

```bash
export GRAFANA_ADMIN_USER=admin
export GRAFANA_ADMIN_PASSWORD=$(ssh -i ~/.ssh/hasan_mighty you@saconsole \
    "sudo grep GRAFANA_ADMIN_PASSWORD /opt/observability/.env" | cut -d= -f2)

python3 orchestration/validate_observability.py
```

All 27 checks must pass. If Loki reports HTTP 503 on the first run, wait
20 seconds and re-run — the Loki ingester has a 15-second warmup period
after a fresh container start.

Expected final line:

```
│ ALL CHECKS PASSED  (27/27 passed) │
```

---

## 8. Take Validated Snapshot

```bash
python3 platforms/kvm/snapshot.py create saconsole "Stage 2.1 Validated"
python3 platforms/kvm/snapshot.py create target1   "Stage 2.1 Validated"

# Confirm
python3 platforms/kvm/snapshot.py list saconsole
python3 platforms/kvm/snapshot.py list target1
```

---

## 9. Access Services

All services are accessible over WireGuard from the controller:

| Service | URL |
|---|---|
| Grafana | http://10.10.0.1:3000 |
| Prometheus | http://10.10.0.1:9090 |
| Alertmanager | http://10.10.0.1:9093 |
| node_exporter (target1) | http://10.10.0.3:9100/metrics |

Grafana credentials are in `/opt/observability/.env` on saconsole.

---

## Snapshot Revert (repeat testing)

To revert both VMs to the baseline and re-run:

```bash
python3 platforms/kvm/snapshot.py revert saconsole "Stage 2.1 Baseline"
python3 platforms/kvm/snapshot.py revert target1   "Stage 2.1 Baseline"

# Start both VMs after revert
python3 platforms/kvm/snapshot.py start saconsole
python3 platforms/kvm/snapshot.py start target1
```

To revert all the way to fresh install and re-run Ansible from scratch:

```bash
python3 platforms/kvm/snapshot.py revert saconsole "Fresh Install"
python3 platforms/kvm/snapshot.py revert target1   "Fresh Install"
./tools/esacp.py provision <hostname>
```
