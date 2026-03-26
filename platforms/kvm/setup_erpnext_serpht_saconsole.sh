#!/usr/bin/env bash
#
# setup_erpnext_serpht_saconsole.sh
# Run from Mighty (controller) — sets up saconsole prerequisites for
# the stg.erpnext.host (serpht / target2) ERPNext install.
#
# What this does on saconsole:
#   1. Creates SSH config entries for t2serpht and t2serpht.r (→ 192.168.122.12)
#   2. Creates key symlinks: you_stg_erpnext_host → id_ed25519
#   3. Creates NVARS file: ~/.ssh/secrets/envars_adm_stg_erpnext_host.sh
#   4. Builds fresh LetsEncrypt tarball from Mighty's letsencrypt_serpht/ directory
#      and uploads to saconsole's ~/.ssh/secrets/
#   5. Uploads supporting secrets: dhparams_4096.pem, daniel_leonard_wild_stapel.p12,
#      ce_sri_parms.json, certbot-cloudflare.ini (dummy — certbot bypassed)
#   6. Adds 192.168.122.12 stg.erpnext.host to saconsole's /etc/hosts
#
# NOTE: Does NOT update /opt/ce_sri/envars.sh symlink on saconsole.
#       That symlink stays pointing to target1's NVARS.
#       prepareServer_0_serpht.sh sources the serpht NVARS file directly.
#
# Usage:
#   cd ~/projects/Logichem/ESACP
#   bash platforms/kvm/setup_erpnext_serpht_saconsole.sh
#
set -euo pipefail

LOGICHEM_DIR="${HOME}/projects/Logichem"
CE_SRI_DIR="${LOGICHEM_DIR}/ce_sri"
EXAMPLE_FILES="${CE_SRI_DIR}/example_srvr_files"
LETSENCRYPT_SRC="${LOGICHEM_DIR}/letsencrypt_serpht"
SACONSOLE="you@10.10.0.1"   # saconsole via WireGuard (192.168.122.10 unreachable from Mighty — virbr0 conflict)

echo "================================================================"
echo " setup_erpnext_serpht_saconsole.sh"
echo " Preparing saconsole for stg.erpnext.host (target2) install"
echo "================================================================"
echo ""

# ── Step 1: Verify letsencrypt_serpht source exists ───────────────────────────
echo "=== Step 1: Verifying fresh SSL cert source ==="
if [[ ! -d "${LETSENCRYPT_SRC}/live/stg.erpnext.host" ]]; then
    echo "ERROR: ${LETSENCRYPT_SRC}/live/stg.erpnext.host not found."
    echo "       Run: ls ${LETSENCRYPT_SRC}"
    exit 1
fi
# Show cert validity
echo "  Cert validity:"
openssl x509 -noout -dates -in "${LETSENCRYPT_SRC}/live/stg.erpnext.host/cert.pem" 2>/dev/null \
    | sed 's/^/    /'
echo ""

# ── Step 2: Build fresh LetsEncrypt tarball from letsencrypt_serpht/ ──────────
echo "=== Step 2: Building fresh LetsEncrypt tarball ==="
LE_TMP=$(mktemp -d)
LE_TGZ="/tmp/letsencrypt.stg.erpnext.host.tgz"

# cp -a preserves relative symlinks (live/ → ../../archive/...)
# These resolve correctly when extracted to /etc/letsencrypt/
mkdir -p "${LE_TMP}/etc"
cp -a "${LETSENCRYPT_SRC}" "${LE_TMP}/etc/letsencrypt"
tar czf "${LE_TGZ}" -C "${LE_TMP}" etc
rm -rf "${LE_TMP}"
echo "  Built: ${LE_TGZ} ($(du -sh ${LE_TGZ} | cut -f1))"

# Verify tarball contains the expected cert paths
echo "  Verifying tarball structure:"
tar -tzf "${LE_TGZ}" | grep "live/stg.erpnext.host" | sed 's/^/    /'
echo ""

# ── Step 3: Upload secrets to saconsole ~/.ssh/secrets/ ───────────────────────
echo "=== Step 3: Uploading secrets to saconsole ==="

ssh ${SACONSOLE} "mkdir -p ~/.ssh/secrets && chmod 700 ~/.ssh/secrets"

# LetsEncrypt tarball (fresh, cert19 valid until May 2026)
scp "${LE_TGZ}" "${SACONSOLE}:~/.ssh/secrets/"
echo "  Uploaded: letsencrypt.stg.erpnext.host.tgz"
rm -f "${LE_TGZ}"

# DH params (real 4096-bit, from example_srvr_files)
scp "${EXAMPLE_FILES}/dhparams_4096.pem" "${SACONSOLE}:~/.ssh/secrets/"
echo "  Uploaded: dhparams_4096.pem"

# SRI digital certificate
scp "${EXAMPLE_FILES}/daniel_leonard_wild_stapel.p12" "${SACONSOLE}:~/.ssh/secrets/"
echo "  Uploaded: daniel_leonard_wild_stapel.p12"

# SRI parms (real ce_sri_parms.json)
scp "${EXAMPLE_FILES}/ce_sri_parms.json" "${SACONSOLE}:~/.ssh/secrets/"
echo "  Uploaded: ce_sri_parms.json"

# Dummy certbot token — needed by moveSecrets() even though certbot is bypassed
ssh ${SACONSOLE} "touch ~/.ssh/secrets/certbot-cloudflare.ini && \
    echo 'dns_cloudflare_api_token = serpht_dummy_not_used' > ~/.ssh/secrets/certbot-cloudflare.ini"
echo "  Created: certbot-cloudflare.ini (dummy — certbot bypassed via letsencrypt backup)"
echo ""

# ── Step 4: Create NVARS file on saconsole ────────────────────────────────────
echo "=== Step 4: Creating NVARS file on saconsole ==="
NVARS_FILE="envars_adm_stg_erpnext_host.sh"

ssh ${SACONSOLE} "cat > ~/.ssh/secrets/${NVARS_FILE} << 'NVARS_EOF'
# Real passwords for stg.erpnext.host (target2) — NEVER COMMIT
# These override CHANGE_ME placeholders in envars_serpht.sh
export ERP_USER_PWD=\"sasa\"
export MYPWD=\"sasa\"
NVARS_EOF
chmod 600 ~/.ssh/secrets/${NVARS_FILE}"
echo "  Created: ~/.ssh/secrets/${NVARS_FILE}"
echo ""

# ── Step 5: Create SSH key symlinks on saconsole ──────────────────────────────
echo "=== Step 5: Creating key symlinks on saconsole ==="
ssh ${SACONSOLE} "
    ln -sf ~/.ssh/id_ed25519     ~/.ssh/you_stg_erpnext_host
    ln -sf ~/.ssh/id_ed25519.pub ~/.ssh/you_stg_erpnext_host.pub
    echo '  you_stg_erpnext_host → id_ed25519'
"
echo ""

# ── Step 6: Add SSH config entries on saconsole ───────────────────────────────
echo "=== Step 6: Adding SSH config entries on saconsole ==="
ssh ${SACONSOLE} '
CONFIG=~/.ssh/config
touch ${CONFIG}
chmod 600 ${CONFIG}

add_host_entry() {
    local MARKER="$1"
    local ENTRY="$2"
    if grep -q "Host ${MARKER}" ${CONFIG} 2>/dev/null; then
        echo "  SSH alias ${MARKER} already in config — skipping"
    else
        printf "\n%s\n" "${ENTRY}" >> ${CONFIG}
        echo "  Added SSH alias: ${MARKER}"
    fi
}

add_host_entry "t2serpht.r" "# Alias for you@target2 (initial root-like access)
Host t2serpht.r
    User you
    HostName 192.168.122.12
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no"

add_host_entry "t2serpht " "# Alias for adm@target2 (ERPNext bench user)
Host t2serpht
    User adm
    HostName 192.168.122.12
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no"
'
echo ""

# ── Step 7: Add /etc/hosts entry on saconsole ─────────────────────────────────
echo "=== Step 7: Adding /etc/hosts entry on saconsole ==="
ssh ${SACONSOLE} "
    if grep -q 'stg.erpnext.host' /etc/hosts 2>/dev/null; then
        echo '  stg.erpnext.host already in /etc/hosts — skipping'
    else
        echo '192.168.122.12  stg.erpnext.host' | sudo tee -a /etc/hosts >/dev/null
        echo '  Added: 192.168.122.12  stg.erpnext.host'
    fi
"
echo ""

# ── Verify ─────────────────────────────────────────────────────────────────────
echo "=== Verification ==="
echo "  Secrets in saconsole:~/.ssh/secrets/"
ssh ${SACONSOLE} "ls -lh ~/.ssh/secrets/ | grep -E 'stg|serpht|dhparams|daniel|ce_sri_parms|certbot' | sed 's/^/    /'"
echo ""
echo "  Key symlinks:"
ssh ${SACONSOLE} "ls -la ~/.ssh/you_stg_erpnext_host* 2>/dev/null | sed 's/^/    /'"
echo ""
echo "  SSH config entries:"
ssh ${SACONSOLE} "grep -A4 't2serpht' ~/.ssh/config 2>/dev/null | sed 's/^/    /'"
echo ""

echo "================================================================"
echo " saconsole is ready for the serpht install."
echo ""
echo " Next steps:"
echo "   1. On toshiba: revert target2 to 'Fresh Install' snapshot"
echo "      ssh toshy bash -c \"virsh --connect qemu:///system snapshot-revert target2 'Fresh Install' --running\""
echo "   2. On saconsole: run the full install"
echo "      ssh saconsole"
echo "      bash ~/projects/ce_sri/development/initialization/prepareServer_0_serpht.sh"
echo "   3. After install completes: take snapshot on toshiba"
echo "      ssh toshy bash -c \"virsh --connect qemu:///system snapshot-create-as target2 'ERPNext v13 Installed' --atomic\""
echo "   4. From Mighty: run the restore"
echo "      cd ~/projects/Logichem/ESACP"
echo "      bash platforms/kvm/provision_erpnext_restore_t2serpht.sh --fresh"
echo "================================================================"
