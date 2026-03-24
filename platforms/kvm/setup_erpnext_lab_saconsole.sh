#!/usr/bin/env bash
# setup_erpnext_lab_saconsole.sh — One-time prerequisite setup on saconsole
# for the ERPNext v13 lab install.
#
# Run from saconsole as user 'you':
#   bash /opt/esacp/platforms/kvm/setup_erpnext_lab_saconsole.sh
#
# Idempotent — safe to re-run.

set -euo pipefail

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "  ✓  $*"; }
skip() { echo "  -  $* (already done)"; }

echo
echo "── ERPNext Lab — saconsole prerequisite setup ──────────────────────────────"
echo

# ── 1. Secrets directory and placeholder files ──────────────────────────────

log "1. Creating ~/.ssh/secrets and placeholder files"
mkdir -p ~/.ssh/secrets

for f in lab_dummy.p12 ce_sri_parms.json; do
    if [[ ! -f ~/.ssh/secrets/${f} ]]; then
        touch ~/.ssh/secrets/${f}
        ok "Created ~/.ssh/secrets/${f}"
    else
        skip "~/.ssh/secrets/${f}"
    fi
done

# DH params — use the real file from example_srvr_files, not an empty placeholder
SCRIPT_DIR_SETUP="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CE_SRI_EXAMPLE="${SCRIPT_DIR_SETUP}/../../ce_sri/example_srvr_files/dhparams_4096.pem"
if [[ ! -f ~/.ssh/secrets/dhparams_4096.pem ]]; then
    if [[ -f "${CE_SRI_EXAMPLE}" ]]; then
        cp "${CE_SRI_EXAMPLE}" ~/.ssh/secrets/dhparams_4096.pem
        ok "Copied real dhparams_4096.pem from example_srvr_files"
    else
        touch ~/.ssh/secrets/dhparams_4096.pem
        echo "  WARNING: example_srvr_files/dhparams_4096.pem not found — empty placeholder created; nginx will fail"
    fi
else
    skip "~/.ssh/secrets/dhparams_4096.pem"
fi

if [[ ! -f ~/.ssh/secrets/certbot-cloudflare.ini ]]; then
    echo "dns_cloudflare_api_token = lab_dummy_not_used" > ~/.ssh/secrets/certbot-cloudflare.ini
    ok "Created ~/.ssh/secrets/certbot-cloudflare.ini"
else
    skip "~/.ssh/secrets/certbot-cloudflare.ini"
fi

# ── 2. Fake LetsEncrypt backup (skips certbot in phase 2) ───────────────────

log "2. Fake LetsEncrypt backup tarball"
LETSTARBALL=~/.ssh/secrets/letsencrypt.lab.target1.local.tgz
if [[ ! -f "${LETSTARBALL}" ]]; then
    mkdir -p /tmp/le_mock/etc/letsencrypt
    tar czf "${LETSTARBALL}" -C /tmp/le_mock .
    rm -rf /tmp/le_mock
    ok "Created ${LETSTARBALL}"
else
    skip "${LETSTARBALL}"
fi

# ── 3. NVARS secrets file (lab-only throwaway passwords) ────────────────────

log "3. NVARS secrets file"
NVARS=~/.ssh/secrets/envars_adm_lab_target1_local.sh
if [[ ! -f "${NVARS}" ]] || ! grep -q "ERP_USER_PWD" "${NVARS}" 2>/dev/null; then
    cat > "${NVARS}" <<'NVARSEOF'
# Lab-only throwaway credentials — replace when moving to a real environment
export ERP_USER_PWD="sasa"
export MYPWD="sasa"
NVARSEOF
    ok "Created ${NVARS} with lab placeholder passwords"
else
    skip "${NVARS} (already has passwords)"
fi

# ── 4. /opt/ce_sri and envars.sh symlink ────────────────────────────────────

log "4. /opt/ce_sri directory and envars.sh symlink"
if [[ ! -d /opt/ce_sri ]]; then
    sudo mkdir -p /opt/ce_sri
    sudo chown you:you /opt/ce_sri
    ok "Created /opt/ce_sri"
else
    skip "/opt/ce_sri"
fi

SYMLINK=/opt/ce_sri/envars.sh
if [[ ! -L "${SYMLINK}" ]]; then
    ln -sf "${NVARS}" "${SYMLINK}"
    ok "Created symlink ${SYMLINK} -> ${NVARS}"
else
    skip "symlink ${SYMLINK}"
fi

# ── 5. SSH key symlinks ──────────────────────────────────────────────────────

log "5. SSH key symlinks"
if [[ ! -L ~/.ssh/you_lab_target1_local ]]; then
    ln -sf ~/.ssh/id_ed25519     ~/.ssh/you_lab_target1_local
    ln -sf ~/.ssh/id_ed25519.pub ~/.ssh/you_lab_target1_local.pub
    ok "Created key symlinks"
else
    skip "Key symlinks already exist"
fi

# ── 6. SSH config entries ────────────────────────────────────────────────────

log "6. SSH config entries"
SSH_CONFIG=~/.ssh/config
touch "${SSH_CONFIG}"

if ! grep -q "Host t1lab.r" "${SSH_CONFIG}" 2>/dev/null; then
    cat >> "${SSH_CONFIG}" <<'SSHCONF'

# ── ERPNext lab target1 ──────────────────────────────────────────────────────
Host t1lab.r
    User you
    HostName 192.168.122.11
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
Host t1lab
    User adm
    HostName 192.168.122.11
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
SSHCONF
    ok "Added t1lab.r and t1lab entries to ~/.ssh/config"
else
    skip "SSH config entries already present"
fi

# ── 7. /etc/hosts entry ──────────────────────────────────────────────────────

log "7. /etc/hosts entry"
if ! grep -q "lab.target1.local" /etc/hosts; then
    echo "192.168.122.11  lab.target1.local" | sudo tee -a /etc/hosts > /dev/null
    ok "Added lab.target1.local to /etc/hosts"
else
    skip "lab.target1.local already in /etc/hosts"
fi

# ── Done ─────────────────────────────────────────────────────────────────────

echo
echo "── Setup complete ───────────────────────────────────────────────────────────"
echo
echo "  Next:"
echo "    bash /opt/esacp/platforms/kvm/bootstrap_erpnext_lab.sh"
echo
