# Prepare KVM Hypervisor Host

Step-by-step checklist for bringing a bare Ubuntu 20.04 machine to the point where
`platforms/kvm/bootstrap_saconsole.sh` can run successfully.

**Status:** Draft — not yet validated on a clean install. Planned test: dual-boot
toshiba (or equivalent) with fresh Ubuntu 20.04 and walk this end-to-end.

A companion script automates controller-side installs and reports hypervisor state:

```bash
bash platforms/kvm/prepare_hypervisor.sh
```

Steps that require a human are marked **[MANUAL]** in the script output.
When all checks pass, `bootstrap_saconsole.sh` will run without errors.

---

## Prerequisites

- Ubuntu 20.04 LTS installed (matches toshiba's documented baseline; osinfo-db
  tops out at `ubuntu20.04` on this release — relevant for `virt-install`)
- Physical access or an out-of-band console for the initial setup
- The controller machine (Mighty or equivalent) reachable on the same LAN
- The secondary storage disk available (LUKS setup is a separate procedure —
  see secondary disk section below)

---

## Part 1 — Hypervisor Host

### 1. Hostname

```bash
sudo hostnamectl set-hostname toshiba
sudo sed -i "s/127.0.1.1.*/127.0.1.1\ttoshiba/" /etc/hosts
```

Verify: `hostname` returns `toshiba`.

### 2. Stable LAN IP

Assign a static IP or create a persistent DHCP reservation on your router for the
machine's MAC address. toshiba uses `192.168.40.16` on interface `wlp2s0`.

Update `/etc/netplan/` or equivalent if configuring statically. Verify:

```bash
ip addr show wlp2s0
```

### 3. SSH daemon

```bash
sudo apt install openssh-server
sudo systemctl enable --now ssh
```

### 4. KVM / libvirt stack

```bash
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients virt-install
sudo systemctl enable --now libvirtd
```

Verify KVM acceleration is available:

```bash
kvm-ok          # from cpu-checker package; optional but useful
virsh --connect qemu:///system version
```

### 5. Add operator user to libvirt group

```bash
sudo usermod -aG libvirt hasan
```

**[MANUAL]** Log out and back in (or `newgrp libvirt`) for the group to take effect.
Verify: `groups | grep libvirt`

### 6. Default libvirt network

```bash
virsh --connect qemu:///system net-autostart default
virsh --connect qemu:///system net-start default
```

Verify: `virsh --connect qemu:///system net-list` shows `default` as active.

### 7. Authorise controller SSH key

**[MANUAL]** This is the only step that requires a password. Run from the controller:

```bash
ssh-copy-id -i ~/.ssh/hasan_mighty.pub hasan@toshiba
```

Verify key auth works (no password prompt):

```bash
ssh -i ~/.ssh/hasan_mighty hasan@toshiba "echo ok"
```

---

## Part 2 — Secondary Disk (LUKS + libvirt pool)

*This section is not part of the 20-step checklist above — it is covered separately.
Documented here for completeness since it must be done before the ISO step.*

The system disk on toshiba is 98% full. All VM images go on a dedicated 1TB disk,
LUKS-encrypted. High-level steps:

1. LUKS format and open the disk
2. Create filesystem: `mkfs.ext4 /dev/mapper/esacp-disk`
3. Add to `/etc/crypttab` (requires passphrase on every reboot — not automated)
4. Add to `/etc/fstab` with mount point `/mnt/esacp-disk`
5. `sudo mkdir -p /mnt/esacp-disk/var/lib/libvirt/images`
6. Create libvirt pool:
   ```bash
   virsh --connect qemu:///system pool-define-as esacp dir \
       --target /mnt/esacp-disk/var/lib/libvirt/images
   virsh --connect qemu:///system pool-start esacp
   virsh --connect qemu:///system pool-autostart esacp
   ```

Verify: `virsh --connect qemu:///system pool-info esacp` shows `State: running`.

**Note:** After every reboot of toshiba, the LUKS disk must be unlocked manually
before any VM operations. The pool will fail to start if the disk is not mounted.

---

## Part 3 — Ubuntu Installation ISO

### 8. Download Ubuntu 24.04.4 live-server ISO

On toshiba (direct download):

```bash
cd /mnt/esacp-disk/var/lib/libvirt/images
wget https://releases.ubuntu.com/24.04.4/ubuntu-24.04.4-live-server-amd64.iso
```

Or transfer from the controller:

```bash
scp ubuntu-24.04.4-live-server-amd64.iso \
    hasan@toshiba:/mnt/esacp-disk/var/lib/libvirt/images/
```

Verify:

```bash
ssh hasan@toshiba "ls -lh /mnt/esacp-disk/var/lib/libvirt/images/*.iso"
```

---

## Part 4 — Controller Machine (Mighty or equivalent)

### 9. SSH keypair for VM access

```bash
ssh-keygen -t ed25519 -f ~/.ssh/hasan_mighty -C "hasan@mighty"
```

### 10. SSH alias for toshiba

Add to `~/.ssh/config`:

```
Host toshy
  User hasan
  HostName toshiba
  IdentityFile ~/.ssh/hasan_mighty
  ServerAliveInterval 120
  ServerAliveCountMax 20
```

### 11. cloud-image-utils

```bash
sudo apt install cloud-image-utils
```

Verify: `cloud-localds --version`

### 12. SOPS + age

Download binaries from GitHub releases and place at `/usr/local/bin/`:

```bash
# sops — https://github.com/getsops/sops/releases
# age  — https://github.com/FiloSottile/age/releases
sudo install -m 755 sops /usr/local/bin/sops
sudo install -m 755 age  /usr/local/bin/age
```

Verify: `sops --version` and `age --version`

### 13. SOPS age key

Place the project age key at `~/.config/sops/age/keys.txt` (mode 0600).
This key decrypts `config/wireguard/keys.sops.yml` during Ansible provisioning.

```bash
mkdir -p ~/.config/sops/age
chmod 700 ~/.config/sops/age
# copy the key file here
chmod 600 ~/.config/sops/age/keys.txt
```

### 14. Ansible

```bash
sudo apt install ansible
```

### 15. Ansible collections

From the project root:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

### 16. ESACP repo

```bash
git clone https://github.com/martinhbramwell/ESACP.git ~/projects/Logichem/ESACP
cd ~/projects/Logichem/ESACP
```

---

## Part 5 — Post-Bootstrap: WireGuard Port-Forward

After `bootstrap_saconsole.sh` completes, Mighty's WireGuard spoke needs to reach
saconsole's hub (192.168.122.10:51820) through toshiba. Two iptables rules are
required on toshiba:

```bash
# Replace wlp2s0 with toshiba's actual LAN interface
sudo iptables -t nat -A PREROUTING -i wlp2s0 -p udp --dport 51820 \
    -j DNAT --to-destination 192.168.122.10:51820
sudo iptables -I FORWARD 1 -i wlp2s0 -o virbr0 -p udp \
    -d 192.168.122.10 --dport 51820 -j ACCEPT
```

**These rules are not persistent across reboots.** Making them persistent via
`iptables-persistent` or a systemd unit is outstanding work (Stage 2.x).

---

## Verification Checklist

Run from the controller once all steps are complete:

```bash
# 1. SSH to toshiba (no password, no prompt)
ssh -i ~/.ssh/hasan_mighty hasan@toshiba "echo ok"

# 2. LUKS disk mounted
ssh hasan@toshiba "mountpoint /mnt/esacp-disk"

# 3. libvirt pool active
ssh hasan@toshiba "virsh --connect qemu:///system pool-info esacp"

# 4. Ubuntu ISO present
ssh hasan@toshiba "test -f /mnt/esacp-disk/var/lib/libvirt/images/ubuntu-24.04.4-live-server-amd64.iso && echo found"

# 5. Default network active
ssh hasan@toshiba "virsh --connect qemu:///system net-list"

# 6. cloud-localds available on controller
cloud-localds --version

# 7. SOPS age key readable
test -f ~/.config/sops/age/keys.txt && echo found

# 8. Run the bootstrap script preflight (exits after checks if you Ctrl-C on Phase 2)
bash platforms/kvm/bootstrap_saconsole.sh
```

If all 8 pass, the host is ready.

---

## Known Constraints

- **osinfo-db on Ubuntu 20.04** tops out at `ubuntu20.04` — `ubuntu22.04` and
  `ubuntu24.04` are absent. `bootstrap_saconsole.sh` uses `--os-variant ubuntu20.04`
  for all VMs on this host regardless of guest OS version.

- **virsh must use `--connect qemu:///system`** — plain `virsh` defaults to user
  session (`qemu:///session`) which cannot access system-level pools or networks.

- **hasan is in `libvirt` group, not `kvm` group** — this is sufficient for
  `qemu:///system` access without sudo when running virsh over SSH.

- **LUKS passphrase required after every reboot** — there is currently no automated
  unlock mechanism. Someone must unlock the disk before VM operations resume.
