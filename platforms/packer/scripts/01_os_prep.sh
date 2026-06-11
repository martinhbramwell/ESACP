#!/usr/bin/env bash
# 01_os_prep.sh — OS preparation for ERPNext v13
#
# Runs INSIDE the build VM as root (via: sudo bash {{ .Path }})
# Mirrors the work of prepareServer_1.sh from the ce_sri repo.
#
# Installs: system packages, MariaDB 10.6, NodeJS 18, wkhtmltopdf, Redis,
#           creates bench user (ERP_USER from ansible/group_vars/all.yml), then reboots.
# Packer waits for SSH to return (expect_disconnect: true) before proceeding.

set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

log() { echo "[01_os_prep $(date '+%H:%M:%S')] $*"; }

# ── Frappe major → OS-specific package choices (ESACP #643) ─────────────────────
# FRAPPE_BRANCH is passed by Packer execute_command (set in erpnext-v13.pkr.hcl).
# v13 builds on Ubuntu 22.04; v15 on 24.04 (noble). Every noble-specific branch
# below is guarded so the v13 (22.04) path runs the EXACT historical commands —
# the v13 build stays byte-identical.
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-13}"
VERSION_MAJOR="${FRAPPE_BRANCH#version-}"

# ── 1. System update ───────────────────────────────────────────────────────────

log "System update ..."
apt-get update -qq
apt-get upgrade -y -qq

# ── 2. Base packages ───────────────────────────────────────────────────────────

log "Installing base packages ..."
apt-get install -y -qq \
    git curl wget unzip jq \
    python3 python3-dev python3-pip python3-setuptools python3-venv \
    build-essential libssl-dev libffi-dev \
    libjpeg-dev zlib1g-dev libpng-dev \
    xfonts-75dpi xfonts-base \
    supervisor cron \
    software-properties-common

# ── 3. MariaDB (10.6 on 22.04 / 10.11 on 24.04 — apt default) ──────────────────
# mariadb-server/client are unversioned: apt installs 10.6 on 22.04, 10.11 on
# 24.04. Only the dev headers differ — v13 used the MySQL dev package; on noble
# the MariaDB dev headers (libmariadb-dev[-compat]) are the correct providers of
# mariadb_config / the mysqlclient build symlinks.

if [[ "${VERSION_MAJOR}" == "13" ]]; then
    log "Installing MariaDB 10.6 ..."
    apt-get install -y -qq \
        mariadb-server mariadb-client \
        libmysqlclient-dev
else
    log "Installing MariaDB 10.11 ..."
    apt-get install -y -qq \
        mariadb-server mariadb-client \
        libmariadb-dev libmariadb-dev-compat
fi

# ERPNext requires these MariaDB settings
cat > /etc/mysql/mariadb.conf.d/99-erpnext.cnf <<'MYCNF'
[mysqld]
character-set-client-handshake = FALSE
character-set-server            = utf8mb4
collation-server                = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
MYCNF

systemctl enable mariadb
systemctl start mariadb

# Set root password to 'erpnext_build' for bench new-site at deploy time.
# This is a build-time placeholder — overwritten during site provisioning.
MARIADB_ROOT_PWD="erpnext_build"
mysql -u root <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED BY '${MARIADB_ROOT_PWD}';
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
FLUSH PRIVILEGES;
SQL
log "✓  MariaDB configured (root pwd: erpnext_build — replaced at deploy time)"

# ── 4. NodeJS (18 on v13 / 20 LTS on v15 / 24 LTS on v16) + yarn ────────────────
# v13 stays on Node 18 (byte-identical); v15 → Node 20 LTS (#643 locked decision);
# v16 → Node 24 LTS — frappe version-16 package.json engines pin "node": ">=24",
# and Node 22 fails v16 asset builds (source-verified, #643 numbat port).

case "${VERSION_MAJOR}" in
    13) NODE_SETUP="18" ;;
    15) NODE_SETUP="20" ;;
    16) NODE_SETUP="24" ;;
    *)  NODE_SETUP="20" ;;
esac
log "Installing NodeJS ${NODE_SETUP} + yarn ..."
curl -fsSL "https://deb.nodesource.com/setup_${NODE_SETUP}.x" | bash -
apt-get install -y -qq nodejs
npm install -g yarn

# ── 5. wkhtmltopdf ────────────────────────────────────────────────────────────

log "Installing wkhtmltopdf 0.12.6 ..."
WKHTML_DEB="wkhtmltox_0.12.6.1-3.jammy_amd64.deb"
WKHTML_URL="https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/${WKHTML_DEB}"
wget -q "${WKHTML_URL}" -O "/tmp/${WKHTML_DEB}"
apt-get install -y -qq "/tmp/${WKHTML_DEB}"
rm -f "/tmp/${WKHTML_DEB}"

# ── 6. Redis ──────────────────────────────────────────────────────────────────

log "Installing Redis ..."
apt-get install -y -qq redis-server
systemctl enable redis-server

# ── 7. nginx ──────────────────────────────────────────────────────────────────

log "Installing nginx ..."
apt-get install -y -qq nginx
systemctl enable nginx

# ── 8. Create bench user ──────────────────────────────────────────────────────
# ERP_USER is passed by Packer via: sudo env ERP_USER=<value> bash {{ .Path }}
# It is read from ansible/group_vars/all.yml by build.sh — not hardcoded here.

ERP_USER="${ERP_USER:?ERP_USER env var not set — pass via Packer execute_command}"

log "Creating bench user '${ERP_USER}' ..."
if ! id "${ERP_USER}" &>/dev/null; then
    useradd -m -s /bin/bash "${ERP_USER}"
    usermod -aG sudo "${ERP_USER}"
    # Passwordless sudo — required for bench setup commands
    echo "${ERP_USER} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${ERP_USER}"
    chmod 440 "/etc/sudoers.d/${ERP_USER}"
fi

# Ensure the bench user has an SSH directory (bench install may need it)
mkdir -p "/home/${ERP_USER}/.ssh"
chown "${ERP_USER}:" "/home/${ERP_USER}/.ssh"
chmod 700 "/home/${ERP_USER}/.ssh"

log "✓  User '${ERP_USER}' ready"

# ── 9–10. frappe-bench CLI ─────────────────────────────────────────────────────
# v13 (22.04): the system Python is writable — upgrade pip, then pip3-install
# bench system-wide (→ /usr/local/bin/bench, on every user's PATH incl. ${ERP_USER}).
# v15 (24.04 noble): PEP-668 marks the system Python externally-managed, so a bare
# `pip3 install` is blocked. --break-system-packages is the sanctioned override; it
# installs bench AND its dependencies — including `uv`, which `bench init` shells
# out to — into /usr/local with their scripts on PATH, mirroring the v13 shape.
# (pipx was tried first but isolates `uv` inside the bench venv, off PATH, so
# `bench init` died with FileNotFoundError: 'uv'.)

if [[ "${VERSION_MAJOR}" == "13" ]]; then
    log "Upgrading pip ..."
    python3 -m pip install --upgrade pip

    log "Installing frappe-bench CLI (pip3) ..."
    pip3 install frappe-bench
else
    log "Installing frappe-bench CLI (pip3 --break-system-packages) ..."
    pip3 install --break-system-packages frappe-bench
fi

# ── Reboot ────────────────────────────────────────────────────────────────────
# Packer expects this disconnect (expect_disconnect: true).
# A clean reboot ensures MariaDB/Redis services start fresh before bench install.

log "OS prep complete — rebooting ..."
reboot
