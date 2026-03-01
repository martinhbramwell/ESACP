# Stage 2.1 ESACP Plan: Alternate Platform with WireGuard

**Date**: 2026-03-01
**Status**: Approved
**Author**: ESACP Project

---

## Context

This stage adds a KVM/Xubuntu provisioning path to ESACP, running in parallel with the existing
VirtualBox/WSL path (Stages 1 & 1.5, untouched). The host machine (`${HOSTNAME}`) is an Xubuntu
workstation with KVM/QEMU/libvirt already operational.

Two new VMs are created:

| VM | OS | Role | Nickname |
|---|---|---|---|
| `saconsole` | Xubuntu 24.04.1 LTS | WireGuard hub · Full observability stack (self + target1) | `sac` |
| `target1` | Ubuntu Server 24.04.4 LTS | WireGuard spoke · Monitored host | `tgt1` |

Both VMs are provisioned via **cloud-init** (OS install, user, SSH, packages, static IP) then
fully configured by **Ansible** (WireGuard, observability stack, node_exporter). The workflow
is repeatable: revert to either baseline snapshot and re-run the provisioner from that point.

The ISOs in the project root are symlinks to their counterparts in `/var/lib/libvirt/images/`:
- `xubuntu-24.04.1-desktop-amd64.iso` → saconsole
- `ubuntu-24.04.4-live-server-amd64.iso` → target1

WireGuard private keys and preshared keys are stored in `config/wireguard/keys.sops.yml`,
encrypted with age via SOPS — the same toolchain used for `ansible/group_vars/all.sops.yml`.

Platform-specific scripts are organised under `platforms/` with stub directories for future
platforms (`vbox/`, `macos/`). The existing `orchestration/` tree is unchanged.

---

## Network Design

```
virbr0  (NAT  192.168.122.0/24)        WireGuard  (10.10.0.0/24)
─────────────────────────────────       ──────────────────────────────
  ${HOSTNAME}  gateway  .1        ←→   10.10.0.2  (spoke)
  saconsole    static   .10       ←→   10.10.0.1  (hub, UDP :51820)
  target1      static   .11       ←→   10.10.0.3  (spoke)

Existing VMs on this host — unaffected.
```

WireGuard overlays the virbr0 network. All Prometheus scraping and Ansible management
of target1 (post-provision) travels over WireGuard IPs.

---

## Snapshot Strategy

Each VM accumulates two named snapshots in sequence:

| Snapshot name | Taken when | State captured |
|---|---|---|
| `"Fresh Install"` | SSH first becomes accessible after cloud-init; before any Ansible | OS, user `<vm-user>`, SSH key, static IP, WireGuard package installed |
| `"Stage 2.1 Baseline"` | After full Ansible provision and WireGuard verified | Fully configured: WireGuard up, observability stack (saconsole) or node_exporter (target1) running |

`provision_kvm.py` automates both: it polls for SSH readiness, takes the `"Fresh Install"`
snapshot, runs Ansible, then takes `"Stage 2.1 Baseline"`. Reverting to `"Fresh Install"`
allows Ansible roles to be re-run and debugged without reinstalling from ISO.

---

## Host Directory — `hosts_map.yml`

`hosts_map.yml` (project root) is the **single source of truth** for all host identities.
Both Ansible inventory and WireGuard peer configs are derived from it. Edit this file, then
run `tools/generate_inventory.py` to regenerate `ansible/inventory/kvm.yml` and the WireGuard
peer list. Do not edit `ansible/inventory/kvm.yml` directly.

Hosts with `ansible_managed: false` appear as WireGuard peers only; playbooks skip them.
This allows manually-configured machines (staff laptops, external nodes) to participate in
the VPN without being provisioned by Ansible.

```yaml
# hosts_map.yml
# Authoritative host directory — source of truth for Ansible and WireGuard.
# Run tools/generate_inventory.py after any change here.

wireguard_subnet: "10.10.0.0/24"
wireguard_port: 51820

groups:

  kvm:
    saconsole:
      hostname: saconsole
      nickname: sac
      wg_ip: "10.10.0.1"
      wg_role: hub
      ansible_managed: true
      platform: kvm
    target1:
      hostname: target1
      nickname: tgt1
      wg_ip: "10.10.0.3"
      wg_role: spoke
      ansible_managed: true
      platform: kvm

  controller:
    local:
      hostname: "${HOSTNAME}"
      nickname: "${HOSTNAME}"
      wg_ip: "10.10.0.2"
      wg_role: spoke
      ansible_managed: false    # Ansible runs FROM here, not against it
      platform: kvm             # set to: kvm | vbox | macos

  # Future groups — define now, activate by populating with hosts
  dev_group: {}
  stage_group: {}
  staff_group: {}
```

---

## Files to Create

```
hosts_map.yml                         # Project root — authoritative host directory

config/
  wireguard/
    generate_keys.sh                  # Generates 3 keypairs + 2 PSKs → writes keys.sops.yml
    keys.sops.yml                     # SOPS/age-encrypted keys (committed to git)

platforms/
  kvm/
    create_seeds.sh                   # cloud-localds wrapper for both VMs
    create_vms.sh                     # virt-install for both VMs
    snapshot.py                       # virsh snapshot lifecycle (create/revert/list/delete)
    cloud-init/
      saconsole/
        user-data                     # autoinstall: hostname, user, SSH key, packages, static IP
        meta-data                     # instance-id, local-hostname
      target1/
        user-data                     # autoinstall: server variant
        meta-data
  vbox/
    PLATFORM.md                       # Stub: existing scripts live in orchestration/
  macos/
    PLATFORM.md                       # Stub: expected tools, approach, known gaps
    create_vms.sh                     # Stub (not functional)
    snapshot.py                       # Stub (not functional)

tools/
  generate_inventory.py               # Reads hosts_map.yml → writes ansible/inventory/kvm.yml
                                      # and renders WireGuard peer lists

orchestration/
  provision_kvm.py                    # KVM provisioner: SSH poll → snapshot → Ansible → snapshot

ansible/
  inventory/kvm.yml                   # Generated — do not edit directly; run generate_inventory.py
  group_vars/kvm.yml                  # ansible_user, SSH key path, WireGuard public keys
  site-kvm.yml                        # Top-level playbook for KVM hosts
  roles/
    wireguard/
      tasks/main.yml                  # Install wireguard-tools, deploy config, enable wg-quick@wg0
      templates/wg0.conf.j2           # Parameterised by wg_role, wg_address, wg_peers
    node_exporter/
      tasks/main.yml                  # Binary install + systemd service (no Docker)
```

---

## Files to Modify

| File | Change |
|---|---|
| `docker/observability/prometheus/prometheus.yml` | Add `node-target1` scrape job (10.10.0.3:9100) |
| `docker/observability/prometheus/alerts/infrastructure.yml` | Verify instance labels work multi-host |
| `docker/observability/prometheus/alerts-drill/infrastructure.yml` | Same |
| `CLAUDE.md` | Update Stage 2 status; document KVM path |
| `/etc/hosts` (host) | Add `saconsole sac` and `target1 tgt1` entries |
| `~/.ssh/config` (host) | Add saconsole + target1 aliases |

---

## Implementation Phases

### Phase 1 — Host Prerequisites

```bash
sudo apt install wireguard wireguard-tools cloud-image-utils genisoimage -y
```

### Phase 2 — WireGuard Key Generation

`config/wireguard/generate_keys.sh` (idempotent — aborts if `keys.sops.yml` already exists):

- Generates private/public keypairs for: controller (`${HOSTNAME}`), `saconsole`, `target1`
- Generates preshared keys: `controller-saconsole.psk`, `target1-saconsole.psk`
- Assembles all into a plaintext YAML structure, encrypts with `sops --encrypt` using the
  project age key (same key as `all.sops.yml`), writes `config/wireguard/keys.sops.yml`
- Prints public keys to stdout — paste into `ansible/group_vars/kvm.yml`

Private keys and PSKs are never stored in plaintext on disk beyond the moment of generation.
Public keys (non-secret) live in `group_vars/kvm.yml` in cleartext.

Ansible tasks on VMs decrypt `keys.sops.yml` via the existing SOPS integration
(`community.sops` lookup or `vars_files` with the SOPS Ansible plugin) to retrieve each
node's private key and PSKs during the `wireguard` role.

`${HOSTNAME}`'s WireGuard is configured by an Ansible play with `connection: local`.

### Phase 3 — Cloud-init user-data

Both VMs use Ubuntu **autoinstall** format (subiquity). Schema:

```yaml
#cloud-config
autoinstall:
  version: 1
  identity:
    hostname: <vm-hostname>
    username: <vm-user>
    # password login disabled — SSH key only
  ssh:
    install-server: true
    authorized-keys:
      - "<content of ${HOME}/.ssh/<keyname>.pub>"
    allow-pw: false
  network:
    version: 2
    ethernets:
      enp1s0:
        addresses: [192.168.122.<x>/24]
        gateway4: 192.168.122.1
        nameservers:
          addresses: [8.8.8.8, 1.1.1.1]
  packages:
    - wireguard
    - wireguard-tools
    - openssh-server
    - curl
    - python3
    # saconsole additionally: docker.io  (Ansible replaces with official Docker CE)
  storage:
    layout:
      name: direct
```

WireGuard configuration is **not** embedded in cloud-init. Ansible applies it post-boot
via the `wireguard` role. Cloud-init remains secrets-free.

### Phase 4 — Seed ISOs

`platforms/kvm/create_seeds.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/../.." && pwd)"

cloud-localds "${PROJ}/platforms/kvm/saconsole-seed.iso" \
  "${PROJ}/platforms/kvm/cloud-init/saconsole/user-data" \
  "${PROJ}/platforms/kvm/cloud-init/saconsole/meta-data"

cloud-localds "${PROJ}/platforms/kvm/target1-seed.iso" \
  "${PROJ}/platforms/kvm/cloud-init/target1/user-data" \
  "${PROJ}/platforms/kvm/cloud-init/target1/meta-data"
```

### Phase 5 — VM Creation and First Snapshots

`platforms/kvm/create_vms.sh` creates both VMs. ISO paths reference the symlinks in the
project root (which point to `/var/lib/libvirt/images/`).

**saconsole** (Xubuntu desktop ISO — `--cdrom` method):

```bash
PROJ="$(cd "$(dirname "$0")/../.." && pwd)"

virt-install \
  --name saconsole --ram 4096 --vcpus 2 \
  --disk path=/var/lib/libvirt/images/saconsole.qcow2,size=20,format=qcow2 \
  --cdrom "${PROJ}/xubuntu-24.04.1-desktop-amd64.iso" \
  --disk path="${PROJ}/platforms/kvm/saconsole-seed.iso",device=cdrom \
  --network network=default \
  --os-variant ubuntu24.04 \
  --graphics vnc --noautoconsole
```

> **One-time manual step**: connect via `virt-viewer saconsole`, press `e` at the GRUB
> menu, append `autoinstall` to the linux kernel line, press F10. Installation then runs
> unattended. Xubuntu 24.04 uses the subiquity installer and supports autoinstall.

**target1** (Ubuntu Server ISO — `--location` method, fully automated):

```bash
virt-install \
  --name target1 --ram 2048 --vcpus 2 \
  --disk path=/var/lib/libvirt/images/target1.qcow2,size=20,format=qcow2 \
  --location "${PROJ}/ubuntu-24.04.4-live-server-amd64.iso" \
  --disk path="${PROJ}/platforms/kvm/target1-seed.iso",device=cdrom \
  --network network=default \
  --os-variant ubuntu24.04 \
  --extra-args "autoinstall ds=nocloud;s=/dev/sr1/" \
  --graphics vnc --noautoconsole
```

**First snapshots** — taken by `provision_kvm.py` immediately after SSH becomes accessible
on each VM (cloud-init complete, OS fresh, no Ansible yet):

```bash
virsh snapshot-create-as saconsole "Fresh Install" --atomic
virsh snapshot-create-as target1   "Fresh Install" --atomic
```

### Phase 6 — Host Configuration

`/etc/hosts` additions:
```
192.168.122.10  saconsole sac
192.168.122.11  target1 tgt1
```

`~/.ssh/config` additions:
```
# -----------------------------------------------------------------------
# Alias configuration: 'saconsole' «begins»
# Alias 'saconsole' binds to remote user <vm-user>@saconsole
Host saconsole sac
  User <vm-user>
  HostName saconsole
  ServerAliveInterval 120
  ServerAliveCountMax 20
  IdentityFile ${HOME}/.ssh/<keyname>
# Alias configuration: 'saconsole' «ends»

# -----------------------------------------------------------------------
# Alias configuration: 'target1' «begins»
# Alias 'target1' binds to remote user <vm-user>@target1
Host target1 tgt1
  User <vm-user>
  HostName target1
  ServerAliveInterval 120
  ServerAliveCountMax 20
  IdentityFile ${HOME}/.ssh/<keyname>
# Alias configuration: 'target1' «ends»
```

### Phase 7 — Inventory Generation and Ansible Roles

`tools/generate_inventory.py` reads `hosts_map.yml` and writes `ansible/inventory/kvm.yml`.
Run this after any change to `hosts_map.yml`. The generated inventory places:
- `saconsole` in groups `kvm`, `development`, `lab` → drill alert profile + full observability
- `target1` in groups `kvm`, `development`, `lab` → node_exporter + wireguard only

The controller node (`${HOSTNAME}`, `ansible_managed: false`) is excluded from the Ansible
inventory but included in the WireGuard peer list consumed by the `wireguard` role.

**`wireguard` role** — configures all three nodes (saconsole as hub, controller + target1 as spokes).

`wg0.conf.j2` renders based on per-host vars:
- `wg_role: hub | spoke`
- `wg_address: 10.10.0.<x>/24`
- `wg_private_key` (decrypted from `keys.sops.yml` at play time)
- `wg_listen_port: 51820` (hub only)
- `wg_peers:` list with `public_key`, `preshared_key`, `endpoint`, `allowed_ips`

UFW: hub opens UDP 51820; target1 opens TCP 9100 from `10.10.0.1` only.

**`node_exporter` role** — target1 only:
- Downloads binary from GitHub releases
- Creates `node_exporter` system user + systemd service
- Port 9100 restricted to saconsole WireGuard IP (`10.10.0.1`) via UFW

**`ansible/site-kvm.yml`** play order:
1. All KVM hosts: `common`, `ssh`, `firewall`, `fail2ban`, `wireguard`
2. saconsole only: `docker`, `observability`
3. target1 only: `node_exporter`
4. Controller (`${HOSTNAME}`, connection: local): `wireguard` (spoke config)

### Phase 8 — Prometheus Extension

Add to `docker/observability/prometheus/prometheus.yml`:

```yaml
- job_name: 'node-target1'
  static_configs:
    - targets: ['10.10.0.3:9100']
      labels:
        host: 'target1'
        env: 'kvm-lab'
```

Existing 7 scrape jobs are unchanged. saconsole self-monitors identically to Stage 1.5.

### Phase 9 — KVM Snapshot Management

`platforms/kvm/snapshot.py` — Python wrapper around virsh:

| Function | virsh command |
|---|---|
| `create(vm, name)` | `virsh snapshot-create-as <vm> <name> --atomic` |
| `revert(vm, name)` | `virsh snapshot-revert <vm> <name>` |
| `list(vm)` | `virsh snapshot-list <vm>` |
| `start(vm)` | `virsh start <vm>` |
| `state(vm)` | `virsh domstate <vm>` |

CLI: `python snapshot.py [create|revert|list] <vm> [name]`

### Phase 10 — Baseline Snapshots

After full Ansible provision and WireGuard verified end-to-end:

```bash
virsh snapshot-create-as saconsole "Stage 2.1 Baseline" --atomic
virsh snapshot-create-as target1   "Stage 2.1 Baseline" --atomic
```

---

## Provisioner Lifecycle (`provision_kvm.py`)

`orchestration/provision_kvm.py` orchestrates the full build sequence for both VMs:

```
For each VM:
  1. Confirm VM exists and is running  (virsh domstate)
  2. Poll SSH until accessible         (timeout 300s, 10s interval)
  3. Take snapshot "Fresh Install"     (virsh snapshot-create-as --atomic)
  4. Run Ansible site-kvm.yml          (ansible-playbook)
  5. Take snapshot "Stage 2.1 Baseline"
  6. Print service URLs
```

Revert to `"Fresh Install"` to re-run Ansible from a clean OS without reinstalling.
Revert to `"Stage 2.1 Baseline"` to reset after chaos scenarios.

---

## macOS Platform Stubs

`platforms/macos/PLATFORM.md` documents the expected implementation approach when macOS
support is activated. Key differences from the KVM path:

| Item | KVM (this stage) | macOS (future) |
|---|---|---|
| Hypervisor | KVM/QEMU via libvirt | Parallels, VMware Fusion, or QEMU/HVF |
| VM lifecycle | `virsh` | `prlctl` / `vmrun` / `qemu-system` |
| Snapshots | `virsh snapshot-*` | Provider-specific |
| WireGuard | `apt install wireguard-tools` | `brew install wireguard-tools` |
| cloud-init | `cloud-localds` + `virt-install` | Provider-dependent |
| SSH key path | `${HOME}/.ssh/<keyname>` | `${HOME}/.ssh/<keyname>` |

`platforms/macos/create_vms.sh` and `platforms/macos/snapshot.py` are non-functional stubs
with `# TODO:` markers at each provider-specific operation.

---

## Verification Checklist

| # | Check | Command |
|---|---|---|
| 1 | `"Fresh Install"` snapshot exists | `virsh snapshot-list saconsole` |
| 2 | SSH to saconsole | `ssh sac` |
| 3 | SSH to target1 | `ssh tgt1` |
| 4 | WireGuard peers on saconsole | `sudo wg show` — 2 peers, recent handshakes |
| 5 | `${HOSTNAME}` → saconsole WG ping | `ping 10.10.0.1` |
| 6 | saconsole → target1 WG ping | `ping 10.10.0.3` (from `ssh sac`) |
| 7 | Prometheus ready | `curl http://saconsole:9090/-/ready` |
| 8 | target1 node job UP | Prometheus targets page |
| 9 | Grafana ready | `curl http://saconsole:3000/api/health` |
| 10 | Multi-host dashboard | node-exporter-full: saconsole + target1 instances |
| 11 | `"Stage 2.1 Baseline"` snapshot exists | `virsh snapshot-list saconsole` |

---

## Constraints and Gotchas

- **Xubuntu GRUB step**: one manual keypress per fresh install (documented in script).
  After that, all configuration is hands-off.
- **WireGuard keys in SOPS**: `keys.sops.yml` is committed and encrypted. Requires the
  project age key (same key used for `all.sops.yml`) to decrypt. If keys are regenerated,
  all WireGuard configs must be re-pushed via Ansible; existing snapshots retain the old config.
- **virbr0 static IPs**: set via cloud-init netplan, not DHCP reservation. Confirm `.10`
  and `.11` are clear of active DHCP leases before VM creation (`virsh net-dhcp-leases default`).
- **target1 firewall**: node_exporter (TCP 9100) restricted to `10.10.0.1` (saconsole WG IP)
  only — not exposed on the virbr0 interface.
- **`hosts_map.yml` is the source of truth**: never edit `ansible/inventory/kvm.yml` directly.
  Always update `hosts_map.yml` and run `tools/generate_inventory.py`.
- **Stage 1/1.5 unchanged**: `orchestration/provision.py`, `orchestration/revertToBaseline.py`,
  `ansible/inventory/dev.yml`, and all VirtualBox-path files are not modified.
