# Saconsole Pre-Rebuild State Capture — 2026-04-18 07:20

Reference snapshot taken before Session A (`fix/222-rebuild-saconsole`) begins
building `platforms/kvm/rebuild_saconsole.sh`. Purpose: record the "before"
state so post-rebuild integrity and blast-radius assertions are anchored.

Not part of the rebuild script; not consumed by any automation.

---

## Libvirt domain (on `toshy`)

| Field | Value |
|---|---|
| Name | `saconsole` |
| UUID | `c3eaf848-fe5d-4c61-9e8a-56337aa555ff` |
| State | `running` (Id 45) |
| CPUs | 2 |
| Memory | 4 GiB |
| Autostart | disabled |
| Security | apparmor enforcing, libvirt-c3eaf848-… |

### Block devices

| Target | Source |
|---|---|
| `vda` | `/mnt/esacp-disk/var/lib/libvirt/images/saconsole.qcow2` (pool `esacp`, capacity 20 GiB, allocation 17.50 GiB, physical 32.50 GiB) |
| `sdb` | `/mnt/esacp-disk/var/lib/libvirt/images/saconsole-seed.iso` (pool `esacp`, 366 KiB) |

### Interfaces

| Interface | Type | Source | Model | MAC |
|---|---|---|---|---|
| `vnet0` | network | `default` | virtio | `52:54:00:05:4b:f8` |

### Snapshots

| Name | Created | State |
|---|---|---|
| `Fresh Install` | 2026-04-15 11:56:01 -0400 | running |
| `Stage 2.2 Baseline` | 2026-04-15 12:07:13 -0400 | running |

### Persistent domain XML

Archived at `~/archives/saconsole/saconsole-pre-rebuild-domain.xml`
(controller-local, not in git).

- 145 lines
- sha256 `a16bf41c02cd11b57002b1f495f462e36d97a4e631c929331a3af2a2e90d60df`

---

## WireGuard peer state — from the hub (saconsole, 10.10.0.1)

- Hub public key: `nn916J0YAufbwZNOKvWs2VX6sV4BKuTqE//985lIiRw=`
- Listen port: `51820`

| Peer pubkey (prefix) | Allowed IPs | Endpoint | Latest handshake |
|---|---|---|---|
| `LUOR6…` | 10.10.0.13/32 (dev01) | 192.168.122.21:45039 | 29s ago |
| `j94AP…` | 10.10.0.2/32 (controller) | 192.168.1.82:35020 | 46s ago |
| `kFwCk…` | 10.10.0.12/32 (dev02) | — | — |
| `9joY/…` | 10.10.0.14/32 (dev03) | — | — |
| `8AFeP…` | 10.10.0.15/32 (target5) | — | — |

Active peers at capture time: dev01 + controller. Others are registered but
the VMs are down (expected — only dev01 running).

### Controller side (Mighty)

- `wg0` IPv4: `10.10.0.2/24`
- Route: `10.10.0.0/24 dev wg0 proto kernel scope link src 10.10.0.2`
- Hub endpoint (from hosts_map): `192.168.122.10` (virbr0-side); external WG
  endpoint used by controller: `192.168.1.79:51820` (toshy).

---

## Controller-side source of truth

These files define saconsole and MUST NOT mutate during the rebuild. Hashes
recorded for post-rebuild comparison.

| File | sha256 |
|---|---|
| `config/wireguard/keys.sops.yml` | `a218d71b2bde3d2e77cdb85e394a0f9ad3979e1bd151ac103a17c56d8fa680de` |
| `hosts_map.yml` | `f6bfd35b8528077d61e799435312bc5a9ce16cffba1b9a2ffb4b679e5e7ff2c3` |

### `hosts_map.yml` saconsole entry (kvm group)

```yaml
saconsole:
  vm_name: saconsole
  hostname: saconsole
  display_name: "Hub Console"
  nickname: sac
  virbr0_ip: "192.168.122.10"
  wg_ip: "10.10.0.1"
  wg_role: hub
  wg_hub_endpoint: "192.168.122.10"
  ansible_managed: true
  backend: kvm
  hypervisor: toshiba
  ansible_groups: [kvm, development, lab]
```

---

## Archive location + retention (agreed this session)

- **Path (controller):** `/home/hasan/archives/saconsole/`
- **Naming:** `saconsole-pre-rebuild-<YYYY-MM-DD-HHMM>.qcow2`, plus matching
  `.xml` (persistent domain) and `.seed.iso`.
- **Transport:** `virsh vol-download` via `qemu:///system` over SSH — no sudo
  needed on toshy; libvirt streams the volume.
- **Retention:** last 3 archives, manually pruned.
- **Not in git** (file sizes far too large; path referenced from the rebuild
  script's header comment only).

---

## Rebuild blast-radius contract

Anything below is expected to SURVIVE rebuild unchanged:

- `hosts_map.yml` (hash above)
- `config/wireguard/keys.sops.yml` (hash above)
- Dev VMs on toshy (currently dev01 running; others defined-but-off)
- Controller WG interface state

Anything below WILL be replaced:

- saconsole libvirt domain definition
- saconsole qcow2 disk + seed ISO
- saconsole's view of its own WG peer table (rebuilt from SOPS + hosts_map via
  `bootstrap_hub.sh`)

---

Captured by: Session A precondition step (issue #222).
