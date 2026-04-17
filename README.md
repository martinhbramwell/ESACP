# ESACP - ERP System Administrator Control Panel

## Overview

ESACP is a multi-stage infrastructure modernization project designed to transform a legacy ERPNext v13 installation into a fully containerized, security-hardened, observable system.

**Current Stage:** Stage 1 - Security-Hardened Foundation

### Stage 1 Goals

- Establish reproducible infrastructure-as-code
- Implement security hardening (SSH, firewall, MFA)
- Deploy containerized observability stack (Grafana, Prometheus, Loki)
- Create documentation-as-code pipeline (YAML → Mermaid diagrams)
- Enable deterministic VM rebuild from snapshots

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   WSL (Controller)               │
│  - Ansible orchestration                         │
│  - Python VM management scripts                  │
│  - SOPS secret encryption                        │
└───────────────┬─────────────────────────────────┘
                │ SSH
                ▼
┌─────────────────────────────────────────────────┐
│         VirtualBox VM (Xubuntu)                  │
│                                                   │
│  ┌──────────────────────────────────────────┐   │
│  │  Nginx (HTTPS + Authelia MFA)            │   │
│  └───────────────┬──────────────────────────┘   │
│                  │                               │
│  ┌───────────────▼──────────────────────────┐   │
│  │  Docker Compose Observability Stack      │   │
│  │  - Grafana (dashboards + Mermaid)        │   │
│  │  - Prometheus + node_exporter            │   │
│  │  - Loki + Promtail (log aggregation)     │   │
│  │  - Alertmanager (Telegram + Email)       │   │
│  │  - Authelia (2FA)                         │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **WSL** with Ubuntu/Debian
- **VirtualBox** installed on Windows
- **Python 3.9+** in WSL
- **Ansible 2.9+** in WSL
- **SOPS** and **age** for secret management
- **GPG** configured for commit signing

### Initial Setup

1. **Install dependencies in WSL:**
   ```bash
   sudo apt update
   sudo apt install ansible python3-pip gpg meld
   pip3 install pyvirtualbox
   
   # Install SOPS
   wget https://github.com/getsops/sops/releases/download/v3.12.1/sops-v3.12.1.linux.amd64
   sudo mv sops-v3.12.1.linux.amd64 /usr/local/bin/sops
   sudo chmod +x /usr/local/bin/sops

   # Install age
   wget https://github.com/FiloSottile/age/releases/download/v1.2.0/age-v1.2.0-linux-amd64.tar.gz
   tar xzf age-v1.2.0-linux-amd64.tar.gz
   sudo mv age/age /usr/local/bin/
   sudo mv age/age-keygen /usr/local/bin/
   ```

2. **Generate age key for SOPS:**
   ```bash
   age-keygen -o ~/.config/sops/age/keys.txt
   # Save the public key for .sops.yaml
   ```

3. **Create baseline VM:**
   - Manually install minimal Ubuntu Server 22.04 LTS in VirtualBox
   - Name: `esacp-dev`
   - Network: Bridged Adapter
   - RAM: 4GB, CPU: 2 cores, Disk: 40GB
   - Enable SSH during install
   - Create user: `admin` (passwordless sudo will be configured by Ansible)
   - Take initial snapshot: `baseline-raw`

4. **Configure Ansible inventory:**
   ```bash
   # Edit ansible/inventory/dev.yml with your VM's IP
   nano ansible/inventory/dev.yml
   ```

5. **Encrypt secrets:**
   ```bash
   # Edit group_vars/all.sops.yml with your secrets
   sops ansible/group_vars/all.sops.yml
   ```

6. **Run provisioning:**
   ```bash
   ./tools/esacp.py provision <hostname>
   ```
   (or drag-to-provision from the Cytoscape control plane)

## Project Structure

```
esacp/
├── ansible/                    # Ansible automation
│   ├── ansible.cfg            # Ansible configuration
│   ├── inventory/             # Environment inventories
│   │   ├── dev.yml           # VirtualBox dev VM
│   │   └── prod.yml          # Future: production VPSes
│   ├── group_vars/           # Variables
│   │   ├── all.yml           # Plain variables
│   │   └── all.sops.yml      # Encrypted secrets
│   ├── roles/                # Ansible roles
│   │   ├── common/           # Base system hardening
│   │   ├── docker/           # Docker installation
│   │   ├── firewall/         # UFW configuration
│   │   ├── ssh/              # SSH hardening
│   │   ├── fail2ban/         # Intrusion prevention
│   │   ├── nginx/            # Reverse proxy + TLS
│   │   ├── observability/    # Monitoring stack
│   │   └── authelia/         # MFA authentication
│   └── site.yml              # Main playbook
├── tools/                    # Unified CLI + pipeline primitives
│   ├── esacp.py              # Dispatcher
│   ├── cli/                  # Per-command entry points
│   └── pipeline/             # Stages + macros (atomic primitives)
├── orchestration/            # Legacy/standalone scripts
│   ├── revertToBaseline.py   # Snapshot restore (VBox-era)
│   └── validate_observability.py  # 27-check harness
├── docker/                   # Container configurations
│   └── observability/
│       ├── docker-compose.yml
│       ├── prometheus/
│       ├── grafana/
│       ├── authelia/
│       ├── loki/
│       └── alertmanager/
├── docs/                     # Documentation
│   ├── architecture.yml      # System architecture (YAML)
│   ├── templates/           # Jinja2 templates
│   └── diagrams/            # Generated Mermaid diagrams
├── scripts/                 # Utility scripts
│   ├── generate_diagrams.py # YAML → Mermaid
│   └── mfa_toggle.sh        # Enable/disable MFA
├── .sops.yaml              # SOPS configuration
└── .gitignore              # Git ignore rules
```

## Development Workflow

### Snapshot-Based Iteration

```bash
# Restore to baseline and apply changes
python3 orchestration/revertToBaseline.py
ansible-playbook -i ansible/inventory/dev.yml ansible/site.yml

# Or use the unified lab CLI
./tools/esacp.py provision <hostname>
```

### Testing Changes

```bash
# Test individual roles
ansible-playbook -i ansible/inventory/dev.yml ansible/site.yml --tags docker

# Dry run
ansible-playbook -i ansible/inventory/dev.yml ansible/site.yml --check

# Verbose output
ansible-playbook -i ansible/inventory/dev.yml ansible/site.yml -vvv
```

### Secrets Management

```bash
# Edit encrypted secrets
sops ansible/group_vars/all.sops.yml

# View encrypted file
sops -d ansible/group_vars/all.sops.yml

# Encrypt new file
sops -e --input-type yaml --output-type yaml file.yml > file.sops.yml
```

## Accessing Services

After provisioning, services are available at:

- **Grafana:** https://VM_IP/ (redirects to /grafana/)
- **Prometheus:** http://VM_IP:9090 (internal only, accessed via Grafana)
- **Alertmanager:** http://VM_IP:9093 (internal only)

### MFA Toggle

```bash
# SSH into VM
ssh admin@VM_IP

# Enable MFA
sudo mfa_on

# Disable MFA
sudo mfa_off
```

## Stage 1 Completion Criteria

- ✅ VM provisioned via Ansible
- ✅ Passwordless sudo configured
- ✅ SSH hardened (key-only, restricted IPs)
- ✅ UFW firewall active (deny incoming, allow 22/443)
- ✅ Fail2ban monitoring SSH
- ✅ Docker + Docker Compose installed
- ✅ Observability stack running
- ✅ Nginx reverse proxy with self-signed TLS
- ✅ Authelia MFA with toggle commands
- ✅ Grafana dashboards for metrics and logs
- ✅ Alertmanager → Telegram integration
- ✅ YAML → Mermaid diagram pipeline
- ✅ All secrets encrypted with SOPS
- ✅ Idempotent playbook execution

## Future Stages

- **Stage 2:** WireGuard mesh network across VPSes
- **Stage 3:** ERPNext v16 containerized deployment
- **Stage 4:** MariaDB master-slave replication
- **Stage 5:** Backup automation and disaster recovery
- **Stage 6:** Production deployment and monitoring

## Contributing

This is a private infrastructure project. Changes should be:
1. Tested on dev VM via snapshot restore
2. Committed with GPG signature
3. Documented in relevant YAML architecture files
4. Validated for idempotency

## License

Private project - All rights reserved.
