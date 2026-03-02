# ESACP — Technical System Overview

Enterprise System Administration & Chaos Planning — Stage 2.1

---

## What It Is

ESACP is a reproducible home-lab infrastructure that automates the provisioning, configuration, and observability of Linux servers, and provides a controlled framework for injecting failures and validating that monitoring detects them. The primary goal is skills development in system administration, infrastructure-as-code, and SRE practices.

---

## Lab Topology (Stage 2.1 — KVM Path)

Two Ubuntu Server 24.04.4 VMs run on KVM/libvirt on an Xubuntu workstation:

| Host | virbr0 IP | WireGuard IP | Role |
|---|---|---|---|
| saconsole | 192.168.122.10 | 10.10.0.1 | WireGuard hub · full observability stack |
| target1 | 192.168.122.11 | 10.10.0.3 | WireGuard spoke · monitored host |
| controller (host) | — | 10.10.0.2 | WireGuard spoke · Ansible runner |

A WireGuard mesh (10.10.0.0/24) overlays the virbr0 NAT network. All Prometheus scraping and Ansible management of target1 travels over WireGuard.

---

## Observability Stack

Runs on saconsole as a Docker Compose stack (`/opt/observability/`):

| Component | Role |
|---|---|
| **Prometheus** (v2.48) | Metrics scraping (8 jobs), alert rule evaluation |
| **Grafana** (v10.2) | Dashboards: Node Exporter Full, cAdvisor, Management Console |
| **Loki** (v2.9) | Log aggregation backend |
| **Promtail** (v3.3) | Log shipping — systemd journal + Docker container logs |
| **Alertmanager** (v0.26) | Alert routing → Telegram |
| **node_exporter** (v1.7) | Host metrics; runs `network_mode: host` so wg0 is visible |
| **cAdvisor** (v0.55) | Container metrics; v0.55+ required for Docker CE 25+ compatibility |

Prometheus scrapes both saconsole (via `host.docker.internal`) and target1 (via WireGuard `10.10.0.3:9100`). On target1, node_exporter runs as a native systemd binary (no Docker). Two alert profiles exist — `production` (long `for:` durations) and `drill` (fast, for lab exercises).

---

## Provisioning Pipeline

```
create_seeds.sh          cloud-localds → seed ISOs (cloud-init user-data/meta-data)
create_vms.sh            virt-install → KVM VMs; autoinstall runs unattended
provision_kvm.py         orchestrates: autoinstall wait → SSH poll →
                           snapshot → Ansible → snapshot
site-kvm.yml             Ansible top-level playbook; 4 plays:
                           all KVM hosts   → common, ssh, firewall, fail2ban, wireguard
                           saconsole only  → docker, observability, desktop
                           target1 only    → node_exporter
                           controller      → wireguard (spoke, localhost connection)
```

Secrets (Grafana password, Telegram token, WireGuard private keys) are stored in SOPS/age-encrypted YAML files committed to the repository. Ansible decrypts them at run time via the `community.sops` collection.

---

## Snapshot Strategy

Each VM has three virsh snapshot points:

1. **Fresh Install** — post cloud-init, pre-Ansible
2. **Stage 2.1 Baseline** — fully configured, WireGuard verified
3. **Stage 2.1 Validated** — 27/27 validation checks passing

`platforms/kvm/snapshot.py` wraps `virsh snapshot-create-as --atomic` and `virsh snapshot-revert` for repeatable chaos exercises.

---

## Validation

`orchestration/validate_observability.py` runs 27 checks across 6 sections (service health, Prometheus scrape targets, metric spot-checks, Loki ingestion, Grafana datasource health, dashboard provisioning). All targets are derived from the project's own config files — nothing is hardcoded.

---

## Controller Platform Support

ESACP is designed to work from four controller environments:

| # | Controller | Hypervisor / Hosts | Status |
|---|---|---|---|
| 1 | Windows 11 + WSL2 | VirtualBox local VMs | Stages 1–1.5 complete |
| 2 | Xubuntu | KVM/libvirt local VMs | Stage 2.1 complete |
| 3 | Ubuntu Server + X2Go | External VPS (iwStack/CloudStack) | Planned |
| 4 | macOS | External VPS (iwStack/CloudStack) | Planned |

Platforms 3 and 4 are controller-only — the managed hosts are external VPS instances provisioned via the CloudStack API. The inventory source of truth (`hosts_map.yml`) is designed to hold both local VMs and remote VPS hosts, with a `backend:` field (`vbox` | `kvm` | `cloudstack`) routing snapshot and lifecycle operations to the correct backend.
