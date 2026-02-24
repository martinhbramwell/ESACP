# ESACP Setup Guide — Stage 1

> **Verified against a clean run on 2026-02-23.**
> All steps reflect the actual working procedure, including lessons learned from
> initial deployment.

---

## ⚠️  Before You Begin — Set Your Environment Variables

Set these variables once at the start of your session. Every command in this
guide uses them so you never have to type hostnames or usernames by hand.

```bash
export ADMIN_USER_NAME="you"                    # Username created during VM installation
export VM_HOSTNAME="esacp-dev"                  # Hostname given to the VM during OS install
export SNAPSHOT_NAME="baseline"                 # Name for the VirtualBox baseline snapshot
export SSH_KEY_PATH="$HOME/.ssh/id_ed25519"     # SSH private key used to connect to the VM

echo "User: ${ADMIN_USER_NAME}  Host: ${VM_HOSTNAME}  Snapshot: ${SNAPSHOT_NAME}  Key: ${SSH_KEY_PATH}"
```

`VM_IP` — the network address assigned to your VM by the router — cannot be
set here because the VM doesn't exist yet. You will find it and set it in
Step 3a. Full instructions are there.

To make all variables permanent across sessions:

```bash
cat >> ~/.bashrc << 'EOF'
export ADMIN_USER_NAME="you"
export VM_HOSTNAME="esacp-dev"
export SNAPSHOT_NAME="baseline"
export SSH_KEY_PATH="$HOME/.ssh/id_ed25519"
EOF
source ~/.bashrc
```

Use `~/.profile` instead of `~/.bashrc` if you need the variables available
in non-interactive or login shells as well.

The Ansible configuration files are set up to derive the username, SSH key,
VM name, and snapshot name from these environment variables automatically.
**The only file you need to manually edit** before provisioning is
`ansible/inventory/dev.yml` — to set your hostname, username, and LAN subnet.
Full instructions are in Step 3b.

---

## Overview

Stage 1 deploys a security-hardened VirtualBox VM running Ubuntu 22.04 with a
full observability stack (Grafana, Prometheus, Loki, Alertmanager, node_exporter,
Promtail, cAdvisor). Provisioning is fully automated via Ansible from your WSL
controller.

**Architecture:**

```
WSL Controller (this machine)
  └── Ansible / SOPS / Python 3
        │ SSH
        ▼
  VirtualBox VM  (${VM_HOSTNAME} — Ubuntu 22.04)
        ├── UFW firewall (SSH restricted to LAN, HTTPS open)
        ├── fail2ban
        ├── Docker Engine
        └── observability_network (bridge)
              ├── Grafana         :3000
              ├── Prometheus      :9090
              ├── Alertmanager    :9093
              ├── Loki            :3100
              ├── Promtail        (no port)
              ├── node_exporter   :9100
              └── cAdvisor        :8080
```

> **Phase A note:** Nginx is installed but not configured as a reverse proxy in
> Stage 1. Access all services directly by IP/hostname and port over HTTP.
> HTTPS / Authelia MFA are Phase B and C goals.

---

## Prerequisites

### Hardware requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Host RAM | 8 GB | 16 GB |
| Host disk (for VDI) | 20 GB free | 40 GB free on a fast drive |
| CPU cores available for VM | 2 | 4 |

> **CRITICAL — Disk space:** Docker image pulls during provisioning consume
> ~12–15 GB. The VirtualBox VDI must live on a drive that has at least 20 GB
> free *after* OS installation. If your C: drive is tight, create the VDI on
> D: or another drive from the start (File → New VM → choose storage location).
> Moving a VDI after creation is possible but requires extra steps (see
> Troubleshooting).

### WSL software requirements

All commands are run from WSL unless stated otherwise.

#### 1. Install Ansible

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible
ansible --version   # expect 2.14+
```

#### 2. Install the community.sops Ansible collection

```bash
ansible-galaxy collection install community.sops
```

#### 3. Install SOPS

SOPS encrypts and decrypts the secrets file. Check
https://github.com/getsops/sops/releases for the latest version before running.

```bash
SOPS_VERSION="3.12.1"
curl -Lo /usr/local/bin/sops \
  "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64"
chmod +x /usr/local/bin/sops
sops --version
```

#### 4. Install age

age is the encryption backend used by SOPS. Check
https://github.com/FiloSottile/age/releases for the latest version.

```bash
AGE_VERSION="1.2.0"
curl -Lo /tmp/age.tar.gz \
  "https://github.com/FiloSottile/age/releases/download/v${AGE_VERSION}/age-v${AGE_VERSION}-linux-amd64.tar.gz"
tar -xf /tmp/age.tar.gz -C /tmp
sudo mv /tmp/age/age /usr/local/bin/age
sudo mv /tmp/age/age-keygen /usr/local/bin/age-keygen
rm -rf /tmp/age /tmp/age.tar.gz
age --version
```

#### 5. Add VBoxManage to WSL PATH

VirtualBox is installed on Windows but its management tool `VBoxManage.exe` is
called from WSL for snapshot operations. Add it to your shell profile:

```bash
echo 'export PATH="$PATH:/mnt/c/Program Files/Oracle/VirtualBox"' >> ~/.bashrc
source ~/.bashrc

VBoxManage.exe --version
```

#### 6. Generate or confirm your SSH key

The provisioner uses the key at `${SSH_KEY_PATH}` to connect to the VM.
Generate one if you don't already have it:

```bash
ssh-keygen -t ed25519 -C "esacp-controller" -f ${SSH_KEY_PATH}

# Print the public key — you will need it in Step 3c
cat ${SSH_KEY_PATH}.pub
```

If you use a key at a different path, set `SSH_KEY_PATH` accordingly —
the provisioner picks it up automatically via the environment variable.
No config files need editing.

#### 7. Generate the age encryption key

SOPS uses an age key pair to encrypt and decrypt `all.sops.yml`. The private
key lives on your controller and never leaves it. The public key goes into
`.sops.yaml` in the project root to tell SOPS which key to use when encrypting.

> **Why the project root?** SOPS searches for `.sops.yaml` starting from the
> directory of the file being encrypted and walks up to the filesystem root.
> Placing it in the project root covers all files in the project. It is possible
> to relocate it by setting the `SOPS_CONFIG_PATH` environment variable, but
> keeping it in the project root is the conventional approach and ensures the
> encryption rules are tracked alongside the code.

```bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt
chmod 600 ~/.config/sops/age/keys.txt

# Print the public key — copy the full age1... string
grep "public key" ~/.config/sops/age/keys.txt
```

The output looks like:

```
# public key: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Open `.sops.yaml` at the project root and replace the existing public key with
yours:

```yaml
creation_rules:
  - path_regex: ansible/group_vars/.*\.sops\.yml$
    age:
      - age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Then re-encrypt `all.sops.yml` so it is bound to your new key:

```bash
sops --rotate --in-place ansible/group_vars/all.sops.yml
```

---

## Step 1 — Create the VirtualBox VM

1. Open VirtualBox → **New**
2. **Name:** `${VM_HOSTNAME}`
3. **Type:** Linux → **Version:** Ubuntu (64-bit)
4. **Memory:** 4096 MB (4 GB) minimum; 8192 MB if available
5. **CPUs:** 2 minimum; 4 recommended
6. **Storage:** Create a new VDI, **dynamically allocated**, **40 GB**
   - Click **Expert Mode** and set the storage location to a drive with
     plenty of free space (e.g. `D:\VM_images\${VM_HOSTNAME}.vdi`)
7. **Network:** Settings → Network → Adapter 1 → **Bridged Adapter**
   (choose your active network card — Ethernet or Wi-Fi)

---

## Step 2 — Install Ubuntu Server 22.04

1. Download **Ubuntu Server 22.04 LTS** ISO from ubuntu.com
2. Attach it: VM Settings → Storage → IDE → select the ISO
3. Boot and follow the installer:
   - Language: English
   - Network: leave as DHCP
   - Storage: use entire disk, no LVM (simpler for a dev VM)
   - **Profile setup:**
     - Your name: anything
     - Server name: `${VM_HOSTNAME}`
     - **Username: `${ADMIN_USER_NAME}`** ← must match your earlier variable
     - Password: something you will remember (needed once for sudo bootstrap)
   - **Featured snaps:** install **OpenSSH server** (check the box)
4. Reboot when prompted. Eject the ISO first.

---

## Step 3 — Configure VM Access

### 3a. Find and set the VM's IP address

Every device on a network is assigned a unique number called an IP address by
the router. You need to find which number your VM was assigned so your
controller can reach it.

Log in to the VM console (VirtualBox window) and run:

```bash
ip addr show
```

Look for a line like `inet 192.168.40.46/24` under the network adapter — the
number before the `/` is the IP address. Now set it in your WSL session:

```bash
export VM_IP="192.168.40.XX"   # replace XX with the actual last numbers
```

### 3b. Edit the inventory file

Open `ansible/inventory/dev.yml` and confirm or update three values to match
your environment:

```yaml
hosts:
  esacp-dev:                        # ← change to ${VM_HOSTNAME} if different
    ansible_user: you               # ← change to ${ADMIN_USER_NAME} if different
    allowed_ssh_ips:
      - "192.168.40.0/24"           # ← change to your LAN subnet if different
```

Your LAN subnet is the same as your VM's IP address but with the last number
replaced by `0` and `/24` appended. For example, if your VM is `192.168.1.46`,
your subnet is `192.168.1.0/24`.

### 3c. Copy your SSH public key to the VM

This allows your controller to log in to the VM without a password:

```bash
ssh-copy-id -i ${SSH_KEY_PATH}.pub ${ADMIN_USER_NAME}@${VM_IP}
```

Test that it worked — you should get a shell prompt without being asked for a
password:

```bash
ssh -i ${SSH_KEY_PATH} ${ADMIN_USER_NAME}@${VM_IP}
exit
```

### 3d. Bootstrap passwordless sudo

Ansible runs all tasks as root (via `sudo`) but cannot type a password
interactively. Grant passwordless sudo once manually — the provisioner will
also manage this going forward.

The `-t` flag allocates an interactive terminal so sudo can prompt for the
password. This will ask for your VM account password one time only.

```bash
ssh -t ${ADMIN_USER_NAME}@${VM_IP} \
  "echo '${ADMIN_USER_NAME} ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/admin_user-nopasswd \
   && sudo chmod 0440 /etc/sudoers.d/admin_user-nopasswd"
```

### 3e. Configure name resolution

Tools on your controller (Ansible, browsers, curl) connect to the VM using the
name `${VM_HOSTNAME}` rather than the raw IP address. Both WSL and Windows need
to know that name maps to the VM's IP.

**WSL** — add to `/etc/hosts`:

```bash
echo "${VM_IP}  ${VM_HOSTNAME}" | sudo tee -a /etc/hosts
```

Test that WSL can reach the VM by name using SSH:

```bash
ssh -i ${SSH_KEY_PATH} ${ADMIN_USER_NAME}@${VM_HOSTNAME}
exit
```

**Windows** — open a terminal as Administrator:

```
Right-click Start → "Terminal (Admin)"
```

PowerShell has its own environment — set these variables to the same values as
your WSL session before running any commands:

```powershell
$VM_IP       = "192.168.40.XX"   # same value as your WSL $VM_IP
$VM_HOSTNAME = "esacp-dev"       # same value as your WSL $VM_HOSTNAME

Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" `
  -Value "$VM_IP  $VM_HOSTNAME"
```

Confirm Windows can reach the VM by name (required for browser access):

```powershell
ping $VM_HOSTNAME -n 2
```

You should see replies, not timeouts.

### 3f. Test Ansible connectivity

```bash
ANSIBLE_CONFIG=ansible/ansible.cfg \
  ansible all -i ansible/inventory/dev.yml -m ping
```

Expected output:

```
${VM_HOSTNAME} | SUCCESS => { "ping": "pong" }
```

---

## Step 4 — Configure Secrets

The file `ansible/group_vars/all.sops.yml` holds all passwords and tokens,
encrypted with your age key. You must populate it before provisioning.

### 4a. Edit the encrypted secrets file

```bash
sops ansible/group_vars/all.sops.yml
```

This opens your `$EDITOR` (nano/vim) with the file decrypted in memory.
Set every value marked `REPLACE` or left blank:

| Variable | Notes |
|----------|-------|
| `grafana_admin_user` | Username for the Grafana UI (e.g. `admin`) |
| `grafana_admin_password` | Strong password — `openssl rand -base64 16` |
| `authelia_jwt_secret` | 64-char random — `openssl rand -base64 48` |
| `authelia_session_secret` | 64-char random — `openssl rand -base64 48` |
| `authelia_storage_encryption_key` | 64-char random — `openssl rand -base64 48` |
| `telegram_bot_token` | From @BotFather on Telegram — see Step 4b |
| `telegram_chat_id` | Negative integer for group chats — see Step 4b |
| `ssl_key_password` | Passphrase for SSL private key |
| `mariadb_root_password` | Future use — set now: `openssl rand -base64 24` |
| `erpnext_admin_password` | Future use — set now |
| `backup_encryption_passphrase` | Future use — set now |

Save and exit — SOPS re-encrypts automatically on save.

### 4b. Set up the Telegram bot (for Alertmanager)

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Save the **bot token** (format: `1234567890:AAxxxxx...`)
4. Create a Telegram group for alerts
5. Add your bot to the group and make it an **admin**
6. Get the **chat ID**:
   - Send any message in the group
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find `"chat":{"id":-1001234567890}` — the negative number is the chat ID
7. Enter both values into `all.sops.yml` via `sops ansible/group_vars/all.sops.yml`

### 4c. Verify the file is properly encrypted

```bash
# Should show encrypted ciphertext, not plaintext
head -5 ansible/group_vars/all.sops.yml
```

The file should contain encrypted values like `ENC[AES256_GCM,...` throughout.

---

## Step 5 — Run Provisioning

From the project root:

```bash
python3 orchestration/provision.py --target dev
```

The script will:
1. Check prerequisites (ansible, sops, age)
2. Wait for SSH to be available
3. Run the full Ansible playbook

### Expected output

The playbook runs ~70 tasks. Successful completion looks like:

```
PLAY RECAP ************************************************************
${VM_HOSTNAME} : ok=67  changed=41  unreachable=0  failed=0  skipped=0
```

All services pull their Docker images on first run (~12–15 GB downloaded).
This is the step most likely to fail if disk space is low.

### Re-running (idempotent)

The playbook is fully idempotent. Re-running after a successful run shows
mostly `ok=67  changed=0`. To run only a specific part:

```bash
python3 orchestration/provision.py --target dev --tags observability
python3 orchestration/provision.py --target dev --tags docker
python3 orchestration/provision.py --target dev --tags security
```

### Dry run

```bash
python3 orchestration/provision.py --target dev --check
```

---

## Step 6 — Verify Services

SSH into the VM:

```bash
ssh ${ADMIN_USER_NAME}@${VM_HOSTNAME}
```

Check all 7 containers are running:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected:

```
NAMES           STATUS          PORTS
grafana         Up X minutes    0.0.0.0:3000->3000/tcp
prometheus      Up X minutes    0.0.0.0:9090->9090/tcp
alertmanager    Up X minutes    0.0.0.0:9093->9093/tcp
loki            Up X minutes    0.0.0.0:3100->3100/tcp
promtail        Up X minutes
node_exporter   Up X minutes    0.0.0.0:9100->9100/tcp
cadvisor        Up X minutes    0.0.0.0:8080->8080/tcp
```

Check service health from WSL:

```bash
curl -s http://${VM_HOSTNAME}:3000/api/health    # {"database": "ok"}
curl -s http://${VM_HOSTNAME}:9090/-/ready       # Prometheus is Ready.
curl -s http://${VM_HOSTNAME}:9093/-/ready       # OK
```

Access Grafana in a browser: `http://${VM_HOSTNAME}:3000`

Log in with the `grafana_admin_user` / `grafana_admin_password` from
`all.sops.yml`.

---

## Step 7 — Take the Baseline Snapshot

Once provisioning succeeds and all services are confirmed healthy, take a
snapshot. This lets you restore to a known-good state if future changes break
the VM.

From WSL (VBoxManage.exe must be in PATH — see Prerequisites §5):

```bash
# Power off cleanly
VBoxManage.exe controlvm ${VM_HOSTNAME} poweroff

# Wait a few seconds, then take the snapshot
VBoxManage.exe snapshot ${VM_HOSTNAME} take ${SNAPSHOT_NAME} \
  --description "Clean provisioned state — Stage 1 complete"

# Confirm
VBoxManage.exe snapshot ${VM_HOSTNAME} list

# Start VM again
VBoxManage.exe startvm ${VM_HOSTNAME} --type headless
```

To restore to baseline at any time:

```bash
python3 orchestration/revertToBaseline.py --vm ${VM_HOSTNAME} --snapshot ${SNAPSHOT_NAME}
```

Or directly:

```bash
VBoxManage.exe controlvm ${VM_HOSTNAME} poweroff
VBoxManage.exe snapshot ${VM_HOSTNAME} restore ${SNAPSHOT_NAME}
VBoxManage.exe startvm ${VM_HOSTNAME} --type headless
```

---

## Troubleshooting

### "VERR_DISK_FULL" during Docker image pulls

The VDI hit the host drive's capacity. Options:

**Option A — Move the VDI to a larger drive.**

Open a terminal as Administrator (Right-click Start → "Terminal (Admin)") and
set PowerShell variables to match your setup:

```powershell
$env:PATH   += ";C:\Program Files\Oracle\VirtualBox"
$USERNAME    = "you"          # your Windows username
$VM_HOSTNAME = "esacp-dev"   # your VM name

VBoxManage modifymedium disk `
  "C:\Users\$USERNAME\VirtualBox VMs\$VM_HOSTNAME\$VM_HOSTNAME.vdi" `
  --move "D:\VM_images\$VM_HOSTNAME.vdi"
```

**Option B — Resize the VDI before reprovisioning:**

```powershell
$VM_HOSTNAME = "esacp-dev"
VBoxManage modifymedium disk "D:\VM_images\$VM_HOSTNAME.vdi" --resize 81920
```

Then expand the partition inside the VM (run from WSL after booting):

```bash
sudo growpart /dev/sda 1 && sudo resize2fs /dev/sda1
```

After fixing disk space, revert to baseline (if snapshot exists) or reprovision
from scratch.

---

### "Missing sudo password"

Ansible cannot escalate to root because passwordless sudo has not been
configured. Run the bootstrap step (3d) first:

```bash
ssh -t ${ADMIN_USER_NAME}@${VM_IP} \
  "echo '${ADMIN_USER_NAME} ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/admin_user-nopasswd \
   && sudo chmod 0440 /etc/sudoers.d/admin_user-nopasswd"
```

---

### "'telegram_bot_token' is undefined"

SOPS is not decrypting `all.sops.yml`. Causes and fixes:

1. **Wrong age key** — The key in `~/.config/sops/age/keys.txt` does not match
   the public key in `.sops.yaml`. Re-generate or restore the original key,
   then re-encrypt: `sops --rotate --in-place ansible/group_vars/all.sops.yml`

2. **Running ansible-playbook directly** — Always use `provision.py`, which
   sets `ANSIBLE_CONFIG` to load the SOPS vars plugin. Running bare
   `ansible-playbook` from the project root will not find `ansible/ansible.cfg`.

3. **community.sops not installed** —
   ```bash
   ansible-galaxy collection install community.sops
   ```

4. **Verify the plugin is enabled:**
   ```bash
   grep vars_plugins_enabled ansible/ansible.cfg
   # Should show: vars_plugins_enabled = host_group_vars,community.sops.sops
   ```

---

### "No config file found; using defaults"

Ansible is not finding `ansible/ansible.cfg`. Always use:

```bash
python3 orchestration/provision.py --target dev
```

Not bare `ansible-playbook site.yml`.

---

### SSH connection refused or timeout

- Confirm the VM is running: VirtualBox Manager or
  `VBoxManage.exe list runningvms`
- Confirm the name resolves: `ping ${VM_HOSTNAME}` from WSL
- Confirm the firewall allows your IP:
  ```bash
  ssh ${ADMIN_USER_NAME}@${VM_HOSTNAME}
  sudo ufw status numbered
  ```
  Your controller's IP must fall within `allowed_ssh_ips` in `dev.yml`.

---

### Grafana redirects to HTTPS (Connection refused on port 443)

In Stage 1, Nginx is not configured as a reverse proxy, so HTTPS does not work.
Check `ansible/group_vars/all.yml`:

```yaml
grafana_root_url: "http://{{ grafana_domain }}:{{ grafana_port }}/"
```

It must use `http`, not `https`. Re-run with the observability tag to apply:

```bash
python3 orchestration/provision.py --target dev --tags observability
```

---

### VBoxManage.exe not found in WSL

```bash
export PATH="$PATH:/mnt/c/Program Files/Oracle/VirtualBox"
VBoxManage.exe --version
```

Add the `export` line to `~/.bashrc` to make it permanent.

---

### revertToBaseline.py fails with "VBoxManage not found"

The revert script calls `VBoxManage` (without `.exe`). Create a permanent alias:

```bash
echo 'alias VBoxManage="VBoxManage.exe"' >> ~/.bashrc
source ~/.bashrc
```

---

## Reference

### Provisioner commands

```bash
# Full provisioning
python3 orchestration/provision.py --target dev

# Dry run (no changes)
python3 orchestration/provision.py --target dev --check

# Single role
python3 orchestration/provision.py --target dev --tags docker
python3 orchestration/provision.py --target dev --tags observability
python3 orchestration/provision.py --target dev --tags security

# Revert to baseline then reprovision
python3 orchestration/provision.py --target dev --revert
```

### Ansible role tags

| Tag | Roles covered |
|-----|---------------|
| `baseline` | common |
| `security` | firewall, ssh, fail2ban, nginx, authelia |
| `docker` | docker |
| `observability` / `monitoring` | observability |
| `mfa` | authelia |

### Service ports (Phase A)

| Service | Port | Notes |
|---------|------|-------|
| Grafana | 3000 | HTTP — login with SOPS credentials |
| Prometheus | 9090 | HTTP — no auth in Phase A |
| Alertmanager | 9093 | HTTP — no auth in Phase A |
| Loki | 3100 | Internal — queried by Grafana |
| node_exporter | 9100 | Internal — scraped by Prometheus |
| cAdvisor | 8080 | Internal — container metrics |
| SSH | 22 | Restricted to `allowed_ssh_ips` subnet |

### Key files

| File | Purpose |
|------|---------|
| `ansible/group_vars/all.yml` | Plain variables (non-secret) |
| `ansible/group_vars/all.sops.yml` | Encrypted secrets (edit via `sops`) |
| `ansible/inventory/dev.yml` | Dev VM connection info — the only file to edit |
| `.sops.yaml` | SOPS encryption rules and age public key |
| `orchestration/provision.py` | Main provisioning script |
| `orchestration/revertToBaseline.py` | Snapshot revert script |
