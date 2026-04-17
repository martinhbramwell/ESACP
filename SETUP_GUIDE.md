# ESACP Setup Guide — Stage 1

> **Status: historical — Stage 1 (VirtualBox / WSL).** Stage 1 was permanently
> retired when the VBox hardware failed on 2026-03-17. The current provisioning
> path is the Gen 3 pipeline — use `./tools/esacp.py provision <hostname>` or
> the Cytoscape control plane. See `README.md` and `docs/BuildOutProcedure.md`
> for the active procedure. The body below is preserved as a record of the
> Stage 1 workflow; commands that reference `orchestration/provision.py` or
> `dev.yml` inventory are from that era and do not map to the current tree.

> **Verified against a clean run on 2026-02-28.**

---

## What This Guide Covers

This guide automates the deployment of Stage 1 of the **ESACP** (ERP System
Administrator Control Panel) project — a security-hardened Ubuntu 22.04 server
running a full observability stack (Grafana, Prometheus, Loki, Alertmanager,
and supporting exporters), all managed via Ansible from a WSL controller on
Windows.

**Expected platform:** Windows 11 with WSL2 as the Ansible controller, and a
VirtualBox VM as the target. Guidance for other platforms is provided in the
appendices.

**This guide assumes you already have** a running Ubuntu 22.04 VM that is
network-accessible from your WSL controller, with a user account, OpenSSH, and
passwordless sudo configured, and a snapshot named **"Ready for Provisioning"**
taken at that clean state. If you do not yet have a suitable VM, see:

- [Appendix 1](#appendix-1--ubuntu-target-guest-in-virtualbox-on-a-windows--wsl-host)
  — VirtualBox on Windows + WSL *(complete)*
- [Appendix 2](#appendix-2--ubuntu-target-guest-in-kvmqemu-on-an-ubuntu-host)
  — KVM/QEMU on Ubuntu host *(coming soon)*
- [Appendix 3](#appendix-3--ubuntu-target-guest-in-kvmqemu-on-an-apple-host)
  — KVM/QEMU on Apple host *(planned)*

---

## A Note on Generic vs. Pre-Configured Use

This repository can be used in two ways:

- **Generic use** — a new operator clones the repo, fills in their own values,
  and generates their own encryption keys. Every file that requires operator
  input has a corresponding `.example` file (see the table below) with
  placeholder values showing exactly what to change.

- **Pre-configured use** — a trusted operator has already configured the repo
  and encrypted the secrets. The recipient receives the repo and the private age
  key separately; they only need to set their environment variables and run the
  provisioner.

| File to configure | Template to copy from |
|-------------------|-----------------------|
| `ansible/inventory/dev.yml` | `ansible/inventory/dev.yml.example` |
| `.sops.yaml` | `.sops.yaml.example` |
| `ansible/group_vars/all.sops.yml` | `ansible/group_vars/all.sops.yml.example` |

If starting from scratch, copy each `.example` file to its real name and fill
in your values before proceeding.

---

## Prerequisites — WSL Controller Software

### 0. Set your environment variables

These variables drive every command in this guide. Set them once per session,
or add them permanently to `~/.bashrc` so they are available in every new
terminal.

Replace every `xxxxx` placeholder with your actual values before running:

```bash
cat >> ~/.bashrc << 'EOF'
export ADMIN_USER_NAME="xxxxxxxxxxx"            # Username created during VM installation
export VM_HOSTNAME="xxxxxxxxxxx"                # Hostname given to the VM during OS install
export VM_IP="xxx.xxx.xxx.xxx"                  # example: "192.168.40.49"
export SSH_KEY_PATH="xxxxxxxxxxxx"              # example: "$HOME/.ssh/id_ed25519"
export SNAPSHOT_NAME="Ready for Provisioning"  # Name of the pre-provisioning VM snapshot
EOF
source ~/.bashrc

# Confirm all variables are set:
echo "User: ${ADMIN_USER_NAME}  Host: ${VM_HOSTNAME}  IP: ${VM_IP}  Key: ${SSH_KEY_PATH}  Snapshot: ${SNAPSHOT_NAME}"
```

The following files also require your input — full instructions appear at the
step where each file is first needed:

| File | What to set | Step |
|------|------------|------|
| `ansible/inventory/dev.yml` | Hostname, username, LAN subnet | Step 1 |
| `.sops.yaml` | Your age public key | Prerequisite §6 |
| `ansible/group_vars/all.sops.yml` | All passwords and tokens | Step 2 |

---

### 1. Install Ansible

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible
ansible --version   # expect 2.14+
```

### 2. Install the community.sops Ansible collection

```bash
ansible-galaxy collection install community.sops
```

### 3. Install SOPS

SOPS encrypts and decrypts the secrets file. Check
https://github.com/getsops/sops/releases for the latest version before running.

```bash
SOPS_VERSION="3.12.1"
curl -Lo /usr/local/bin/sops \
  "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64"
sudo chmod +x /usr/local/bin/sops
sops --version
```

### 4. Install age

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

### 5. Confirm your SSH key

The provisioner uses the private key at `${SSH_KEY_PATH}` to connect to the VM.
You most likely already have one — confirm it exists:

```bash
ls -la ${SSH_KEY_PATH} ${SSH_KEY_PATH}.pub
```

If you do not have a key yet, generate one:

```bash
# Only run this if the key does not already exist:
ssh-keygen -t ed25519 -C "esacp-controller" -f ${SSH_KEY_PATH}
```

If you use a key at a different path, update `SSH_KEY_PATH` accordingly.
No config files need editing — the provisioner picks it up automatically.

### 6. Generate the age encryption key

SOPS uses an age key pair to encrypt and decrypt `all.sops.yml`. The private
key lives on your controller and never leaves it. The public key goes into
`.sops.yaml` to tell SOPS which key to use when encrypting.

> **Why the project root?** SOPS searches for `.sops.yaml` starting from the
> directory of the file being encrypted and walks up to the filesystem root.
> Placing it in the project root covers all files in the project. It is possible
> to relocate it via `SOPS_CONFIG_PATH`, but the project root is the
> conventional and simplest approach.

```bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt
chmod 600 ~/.config/sops/age/keys.txt

# Print the public key — copy the full age1... string
grep "public key" ~/.config/sops/age/keys.txt
```

Output looks like:

```
# public key: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Open `.sops.yaml` at the project root (use `.sops.yaml.example` as your
starting point) and replace the placeholder with your public key:

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

### 7. Confirm name resolution

Your WSL controller must reach the VM by hostname (not just IP), because
Ansible uses the hostname from the inventory file.

Add the VM to WSL's hosts file:

```bash
echo "${VM_IP}  ${VM_HOSTNAME}" | sudo tee -a /etc/hosts
```

Test from WSL:

```bash
ssh -i ${SSH_KEY_PATH} ${ADMIN_USER_NAME}@${VM_HOSTNAME}
exit
```

### 8. Install Python dependencies

The orchestration scripts and diagram generator require three Python packages.
`rich` is also required by the Stage 1.5 chaos drill scripts.

On Ubuntu / WSL, install via `apt` (the system Python on Ubuntu 22.04+ is
PEP 668 managed and rejects `pip` installs into the system environment):

```bash
sudo apt install -y python3-rich python3-yaml python3-jinja2
```

Confirm all three are importable:

```bash
python3 -c "import rich, yaml, jinja2; print('OK')"
```

> **Non-Ubuntu platforms:** Use `pip install -r orchestration/requirements.txt`
> (with a virtual environment if your system enforces PEP 668).

---

## Step 1 — Edit the Inventory File

Copy the example file if you have not already:

```bash
cp ansible/inventory/dev.yml.example ansible/inventory/dev.yml
```

Open `ansible/inventory/dev.yml` and set these three values to match your
environment:

```yaml
hosts:
  xxxxxxxxxxx:                      # ← your VM_HOSTNAME
    ansible_user: xxxxxxxxxxx       # ← your ADMIN_USER_NAME
    allowed_ssh_ips:
      - "xxx.xxx.xxx.0/24"          # ← your LAN subnet
```

Your LAN subnet is your VM's IP with the last number replaced by `0` and
`/24` appended. For example, if `VM_IP` is `192.168.40.49`, the subnet is
`192.168.40.0/24`.

### Test Ansible connectivity

```bash
ANSIBLE_CONFIG=ansible/ansible.cfg \
  ansible all -i ansible/inventory/dev.yml -m ping
```

Expected output (the callback format changed in community.general 12+):

```
PLAY [Ansible Ad-Hoc] **********************************************************

TASK [ping] ********************************************************************
ok: [console]

PLAY RECAP *********************************************************************
console : ok=1  changed=0  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

If you see `failed=1` or `unreachable=1`, see the Troubleshooting section.

---

## Step 2 — Configure Secrets

`ansible/group_vars/all.sops.yml` holds all passwords and tokens, encrypted
with your age key. Copy the example structure if starting from scratch:

```bash
cp ansible/group_vars/all.sops.yml.example ansible/group_vars/all.sops.yml
sops ansible/group_vars/all.sops.yml
```

The `sops` command opens your `$EDITOR` with the file decrypted in memory.
Set every value marked `REPLACE`:

| Variable | Notes |
|----------|-------|
| `grafana_admin_user` | Username for the Grafana UI (e.g. `admin`) |
| `grafana_admin_password` | Strong password — `openssl rand -base64 16` |
| `authelia_jwt_secret` | 64-char random — `openssl rand -base64 48` |
| `authelia_session_secret` | 64-char random — `openssl rand -base64 48` |
| `authelia_storage_encryption_key` | 64-char random — `openssl rand -base64 48` |
| `telegram_bot_token` | From @BotFather on Telegram — see Step 2b |
| `telegram_chat_id` | Negative integer for group chats — see Step 2b |
| `ssl_key_password` | Passphrase for SSL private key |
| `mariadb_root_password` | Future use — set now: `openssl rand -base64 24` |
| `erpnext_admin_password` | Future use — set now |
| `backup_encryption_passphrase` | Future use — set now |

Save and exit — SOPS re-encrypts automatically on save.

### 2b. Set up the Telegram bot (for Alertmanager)

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Save the **bot token** (format: `1234567890:AAxxxxx...`)
4. Create a Telegram group for alerts
5. Add your bot to the group and make it an admin
6. Get the **chat ID**:
   - Send any message in the group
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find `"chat":{"id":-1001234567890}` — the negative number is the chat ID
7. Enter both values via `sops ansible/group_vars/all.sops.yml`

### 2c. Verify encryption

```bash
head -5 ansible/group_vars/all.sops.yml
```

Should show encrypted ciphertext (`ENC[AES256_GCM,...`), not plaintext.

---

## Step 3 — Run Provisioning

```bash
python3 orchestration/provision.py --target dev
```

The script checks prerequisites, waits for SSH, then runs the full Ansible
playbook (~70 tasks). The first run downloads ~12–15 GB of Docker images.

### Expected output

```
PLAY RECAP *********************************************************************
console : ok=70  changed=41  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

### Re-running (idempotent)

The playbook is fully idempotent. Re-running after a successful run shows
mostly `ok=70  changed=0`. To run only a specific part:

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

## Step 4 — Verify Services

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
curl -s http://${VM_HOSTNAME}:3000/api/health    # Grafana:      {"database": "ok"}
curl -s http://${VM_HOSTNAME}:9090/-/ready       # Prometheus:   Prometheus is Ready.
curl -s http://${VM_HOSTNAME}:9093/-/ready       # Alertmanager: OK
```

Access Grafana in a browser: `http://${VM_HOSTNAME}:3000`

Log in with the `grafana_admin_user` / `grafana_admin_password` set in
`all.sops.yml`.

---

## Step 5 — Take the Post-Provisioning Snapshot

Once all services are confirmed healthy, take a snapshot. From WSL:

```bash
VBoxManage.exe controlvm ${VM_HOSTNAME} poweroff
sleep 5
VBoxManage.exe snapshot ${VM_HOSTNAME} take "Stage 1 Complete" \
  --description "Fully provisioned Stage 1 — ok=70 changed=41 failed=0"
VBoxManage.exe snapshot ${VM_HOSTNAME} list
VBoxManage.exe startvm ${VM_HOSTNAME} --type headless
```

To restore to the pre-provisioning baseline at any time:

```bash
VBoxManage.exe controlvm ${VM_HOSTNAME} poweroff
VBoxManage.exe snapshot ${VM_HOSTNAME} restore "${SNAPSHOT_NAME}"
VBoxManage.exe startvm ${VM_HOSTNAME} --type headless
```

---

## Troubleshooting

### SSH connection refused

OpenSSH is not installed on the VM. Log into the VM console directly
(VirtualBox window) and run:

```bash
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
```

Then return to Prerequisite §7.

### "Missing sudo password"

Ansible cannot escalate to root. Run the bootstrap from Appendix 1 §A1-6, or
directly:

```bash
ssh -t ${ADMIN_USER_NAME}@${VM_IP} \
  "echo '${ADMIN_USER_NAME} ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/admin_user-nopasswd \
   && sudo chmod 0440 /etc/sudoers.d/admin_user-nopasswd"
```

### "VERR_DISK_FULL" during Docker image pulls

**Option A — Move the VDI to a larger drive** (run as Administrator in PowerShell):

```powershell
$env:PATH   += ";C:\Program Files\Oracle\VirtualBox"
$USERNAME    = "you"        # your Windows username
$VM_HOSTNAME = "console"   # your VM name

VBoxManage modifymedium disk `
  "C:\Users\$USERNAME\VirtualBox VMs\$VM_HOSTNAME\$VM_HOSTNAME.vdi" `
  --move "D:\VM_images\$VM_HOSTNAME.vdi"
```

**Option B — Resize the VDI:**

```powershell
$VM_HOSTNAME = "console"
VBoxManage modifymedium disk "D:\VM_images\$VM_HOSTNAME.vdi" --resize 81920
```

Then expand the partition inside the VM:

```bash
sudo growpart /dev/sda 1 && sudo resize2fs /dev/sda1
```

### "'telegram_bot_token' is undefined"

SOPS is not decrypting `all.sops.yml`. Causes and fixes:

1. **Wrong age key** — The key in `~/.config/sops/age/keys.txt` does not match
   the public key in `.sops.yaml`. Restore the correct key, then re-encrypt:
   `sops --rotate --in-place ansible/group_vars/all.sops.yml`

2. **Running ansible-playbook directly** — Always use `provision.py`, which
   sets `ANSIBLE_CONFIG` to load the SOPS vars plugin.

3. **community.sops not installed** —
   ```bash
   ansible-galaxy collection install community.sops
   ```

### "No config file found; using defaults"

Always provision via:

```bash
python3 orchestration/provision.py --target dev
```

Not bare `ansible-playbook site.yml`.

### SSH connection timeout after provisioning

Your controller's IP must fall within `allowed_ssh_ips` in `dev.yml`. Check:

```bash
ssh ${ADMIN_USER_NAME}@${VM_HOSTNAME} "sudo ufw status numbered"
```

### Grafana redirects to HTTPS (port 443 refused)

In Stage 1, Nginx is not configured as a reverse proxy. Verify
`ansible/group_vars/all.yml` uses `http`:

```yaml
grafana_root_url: "http://{{ grafana_domain }}:{{ grafana_port }}/"
```

Then re-run: `python3 orchestration/provision.py --target dev --tags observability`

### VBoxManage.exe not found in WSL

```bash
export PATH="$PATH:/mnt/c/Program Files/Oracle/VirtualBox"
VBoxManage.exe --version
```

Add the `export` line to `~/.bashrc` to make it permanent.

### revertToBaseline.py fails with "VBoxManage not found"

```bash
echo 'alias VBoxManage="VBoxManage.exe"' >> ~/.bashrc
source ~/.bashrc
```

---

## Reference

### Provisioner commands

```bash
python3 orchestration/provision.py --target dev               # Full provisioning
python3 orchestration/provision.py --target dev --check       # Dry run
python3 orchestration/provision.py --target dev --tags docker
python3 orchestration/provision.py --target dev --tags observability
python3 orchestration/provision.py --target dev --tags security
python3 orchestration/provision.py --target dev --revert      # Revert then reprovision
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
| `ansible/inventory/dev.yml` | Dev VM connection info |
| `.sops.yaml` | SOPS encryption rules and age public key |
| `orchestration/provision.py` | Main provisioning script |
| `orchestration/revertToBaseline.py` | Snapshot revert script |

---

---

# Appendix 1 — Ubuntu Target Guest in VirtualBox on a Windows + WSL Host

This appendix walks through creating and preparing a Ubuntu 22.04 VM in
VirtualBox on Windows, using WSL as the Ansible controller. The end result is
a VM with a **"Ready for Provisioning"** snapshot that the main guide expects.

---

## A1-1. Add VBoxManage to your WSL PATH

VirtualBox is installed on Windows but its management tool `VBoxManage.exe`
is called from WSL. Add it to your shell profile once:

```bash
echo 'export PATH="$PATH:/mnt/c/Program Files/Oracle/VirtualBox"' >> ~/.bashrc
source ~/.bashrc
VBoxManage.exe --version
```

---

## A1-2. Create the VM

1. Open VirtualBox → **New**
2. **Name:** your `${VM_HOSTNAME}` value
3. **Type:** Linux → **Version:** Ubuntu (64-bit)
4. **Memory:** 4096 MB minimum; 8192 MB recommended
5. **CPUs:** 2 minimum; 4 recommended
6. **Storage:** Create a new VDI, dynamically allocated, **40 GB**
   - In Expert Mode, set the storage location to a drive with plenty of free
     space (e.g. `D:\VM_images\${VM_HOSTNAME}.vdi`)

> **Disk warning:** Docker image pulls consume ~12–15 GB. The VDI must live on
> a drive with at least 20 GB free *after* OS installation.

7. **Network:** Settings → Network → Adapter 1 → **Bridged Adapter**, then
   choose your active physical network adapter (Ethernet or Wi-Fi).

> **Critical — snapshots capture network settings:** Set the network adapter to
> Bridged **before taking any snapshot**. Restoring a snapshot taken while the
> adapter was NAT will silently revert to NAT, and the VM will lose network
> access from WSL.
>
> **If you restore a snapshot and find NAT is active**, no work is lost. Power
> off the VM, switch the adapter, and start again — the snapshot contents are
> unaffected:
>
> ```bash
> VBoxManage.exe controlvm ${VM_HOSTNAME} poweroff
> VBoxManage.exe modifyvm ${VM_HOSTNAME} --nic1 bridged \
>   --bridgeadapter1 "Your Adapter Name Here"
> VBoxManage.exe startvm ${VM_HOSTNAME} --type headless
> ```
>
> To find available adapter names:
> `VBoxManage.exe list bridgedifs | grep "^Name:"`

---

## A1-3. Install Ubuntu Server 22.04

Download the **Ubuntu Server 22.04 LTS** ISO from ubuntu.com and attach it:
VM Settings → Storage → IDE → select the ISO.

There are two installation paths — choose one.

### Path A — Guided installer (recommended)

Boot the VM and follow the interactive installer:

- Language: English
- Network: leave as DHCP
- Storage: use entire disk, no LVM
- **Profile setup:**
  - Server name: your `${VM_HOSTNAME}`
  - **Username:** your `${ADMIN_USER_NAME}` ← must match your environment variable
  - Password: something you will remember (needed once for the sudo bootstrap below)
- **Featured Server Snaps:** check **OpenSSH server** ← do not skip this

Reboot when prompted and eject the ISO.

### Path B — VirtualBox unattended installer

VirtualBox's built-in unattended installer (Right-click VM → **Unattended
Install**) automates the OS installation but **does not install OpenSSH**.
After the VM boots, log in at the VirtualBox console and install it:

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
systemctl is-active ssh    # should print: active
```

> **Unattended installer username:** VirtualBox creates a user named `vboxuser`
> by default. If you need a different username to match `${ADMIN_USER_NAME}`,
> change it in the unattended install dialog before starting, or rename the
> user after installation.

---

## A1-4. Find the VM's IP address

Log into the VM console (VirtualBox window) and run:

```bash
ip addr show
```

Look for a line like `inet 192.168.40.49/24` — the number before `/` is the IP.
Set it in your WSL session (and in `~/.bashrc`):

```bash
export VM_IP="192.168.40.49"   # replace with your actual IP
```

---

## A1-5. Copy your SSH public key to the VM

SSH key authentication allows your WSL controller to log in to the VM account
more securely and conveniently than with a password — the key proves your
identity cryptographically, without transmitting a password over the network.

```bash
ssh-copy-id -i ${SSH_KEY_PATH}.pub ${ADMIN_USER_NAME}@${VM_IP}
```

Enter the VM account password when prompted. This is the last time you will
need it. Test that key authentication works:

```bash
ssh -i ${SSH_KEY_PATH} ${ADMIN_USER_NAME}@${VM_IP}
exit
```

You should get a shell prompt without being asked for a password.

---

## A1-6. Bootstrap passwordless sudo

The `sudo` command allows specified users to run tasks with root (system
administrator) privileges. The `sudoers` configuration controls exactly which
users can do what. Ansible needs to run most provisioning tasks as root via
`sudo`, but is not able to type passwords interactively.

This command grants passwordless sudo to your account once, manually — Ansible
will then manage the sudoers configuration going forward.

The `-t` flag is required: it allocates an interactive terminal so that `sudo`
can prompt for your password. You will be asked for your VM account password
one time only.

```bash
ssh -t ${ADMIN_USER_NAME}@${VM_IP} \
  "echo '${ADMIN_USER_NAME} ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/admin_user-nopasswd \
   && sudo chmod 0440 /etc/sudoers.d/admin_user-nopasswd"
```

Verify it worked — should print `SUDO_OK` without prompting for a password:

```bash
ssh -i ${SSH_KEY_PATH} ${ADMIN_USER_NAME}@${VM_IP} "sudo -n echo SUDO_OK"
```

---

## A1-7. Configure name resolution

Both WSL and Windows need to map the VM hostname to its IP address.

**WSL** — add to `/etc/hosts`:

```bash
echo "${VM_IP}  ${VM_HOSTNAME}" | sudo tee -a /etc/hosts
```

Test from WSL:

```bash
ssh -i ${SSH_KEY_PATH} ${ADMIN_USER_NAME}@${VM_HOSTNAME}
exit
```

**Windows** — open Terminal as Administrator:

```
Right-click Start → "Terminal (Admin)"
```

PowerShell has its own environment — declare these variables before running
any commands (they do not carry over from WSL):

```powershell
$VM_IP       = "192.168.40.49"   # match your WSL $VM_IP
$VM_HOSTNAME = "console"         # match your WSL $VM_HOSTNAME

Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" `
  -Value "$VM_IP  $VM_HOSTNAME"
```

Confirm Windows can resolve the name (required for browser access):

```powershell
ping $VM_HOSTNAME -n 2
```

You should see replies, not timeouts.

---

## A1-8. Take the "Ready for Provisioning" snapshot

With OpenSSH running, the SSH key authorised, and passwordless sudo confirmed,
the VM is in the correct state for snapshotting. This snapshot is the restore
point you will revert to whenever you need a clean slate before reprovisioning.

```bash
VBoxManage.exe controlvm ${VM_HOSTNAME} poweroff
sleep 5
VBoxManage.exe snapshot ${VM_HOSTNAME} take "Ready for Provisioning" \
  --description "OpenSSH installed, SSH key authorised, NOPASSWD sudo configured. Bridged adapter confirmed."
VBoxManage.exe snapshot ${VM_HOSTNAME} list
VBoxManage.exe startvm ${VM_HOSTNAME} --type headless
```

You are now ready to return to the main guide and begin from **Step 1**.

---

---

# Appendix 2 — Ubuntu Target Guest in KVM/QEMU on an Ubuntu Host

*Coming soon.*

---

---

# Appendix 3 — Ubuntu Target Guest in KVM/QEMU on an Apple Host

*Planned.*

> **Note:** macOS itself cannot be installed as a guest in VirtualBox or any
> other hypervisor on non-Apple hardware — Apple's EULA restricts macOS to
> Apple-branded hardware, and VirtualBox has no official macOS guest support.
> This appendix covers running a *Linux* guest on an Apple host, not macOS in
> a VM.
