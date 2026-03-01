#!/usr/bin/env bash
# generate_keys.sh — WireGuard key generation for ESACP Stage 2.1
#
# Generates keypairs for: controller (${HOSTNAME}), saconsole, target1
# Generates preshared keys for: controller↔saconsole, target1↔saconsole
#
# Output: config/wireguard/keys.sops.yml  (age-encrypted via SOPS, safe to commit)
#
# Usage:
#   cd <project-root>
#   bash config/wireguard/generate_keys.sh
#
# Prerequisites: wg, sops, age key configured in ~/.config/sops/age/keys.txt
# Idempotent: aborts if keys.sops.yml already exists.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
KEYS_FILE="${SCRIPT_DIR}/keys.sops.yml"
SOPS_CONF="${PROJ_ROOT}/.sops.yaml"

# ── Preflight ────────────────────────────────────────────────────────────────

if [[ -f "${KEYS_FILE}" ]]; then
    echo "ERROR: ${KEYS_FILE} already exists."
    echo "       Delete it first if you want to regenerate all keys."
    echo "       WARNING: regenerating invalidates all existing WireGuard configs."
    exit 1
fi

for cmd in wg sops; do
    if ! command -v "${cmd}" &>/dev/null; then
        echo "ERROR: '${cmd}' not found. Install it and retry."
        exit 1
    fi
done

if [[ ! -f "${SOPS_CONF}" ]]; then
    echo "ERROR: ${SOPS_CONF} not found. Run from the project root or fix SOPS config."
    exit 1
fi

# Extract age recipient from .sops.yaml
AGE_RECIPIENT=$(grep -oP 'age1[a-z0-9]+' "${SOPS_CONF}" | head -1)
if [[ -z "${AGE_RECIPIENT}" ]]; then
    echo "ERROR: No age recipient found in ${SOPS_CONF}."
    exit 1
fi

# ── Key generation ───────────────────────────────────────────────────────────

echo "Generating WireGuard keys..."

CONTROLLER_PRIV=$(wg genkey)
SACONSOLE_PRIV=$(wg genkey)
TARGET1_PRIV=$(wg genkey)

CONTROLLER_PUB=$(echo "${CONTROLLER_PRIV}" | wg pubkey)
SACONSOLE_PUB=$(echo "${SACONSOLE_PRIV}"  | wg pubkey)
TARGET1_PUB=$(echo "${TARGET1_PRIV}"      | wg pubkey)

CONTROLLER_SACONSOLE_PSK=$(wg genpsk)
TARGET1_SACONSOLE_PSK=$(wg genpsk)

# ── Encrypt and write ─────────────────────────────────────────────────────────

TMPFILE=$(mktemp --suffix=.sops.yml)
trap 'rm -f "${TMPFILE}" "${KEYS_FILE}.tmp"' EXIT

cat > "${TMPFILE}" <<YAML
# WireGuard keys — ESACP Stage 2.1
# Encrypted with SOPS/age. Safe to commit.
# Regenerate with: bash config/wireguard/generate_keys.sh  (after deleting this file)

controller:
    private_key: "${CONTROLLER_PRIV}"
    public_key:  "${CONTROLLER_PUB}"

saconsole:
    private_key: "${SACONSOLE_PRIV}"
    public_key:  "${SACONSOLE_PUB}"

target1:
    private_key: "${TARGET1_PRIV}"
    public_key:  "${TARGET1_PUB}"

preshared_keys:
    controller_saconsole: "${CONTROLLER_SACONSOLE_PSK}"
    target1_saconsole:    "${TARGET1_SACONSOLE_PSK}"
YAML

sops --encrypt \
     --age "${AGE_RECIPIENT}" \
     --input-type yaml \
     --output-type yaml \
     "${TMPFILE}" > "${KEYS_FILE}.tmp" && mv "${KEYS_FILE}.tmp" "${KEYS_FILE}"

# Temp file with plaintext keys is removed by trap on exit.

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "✅  config/wireguard/keys.sops.yml written and encrypted."
echo ""
echo "Public keys — paste into ansible/group_vars/kvm.yml:"
echo ""
echo "    wg_pubkey_controller: \"${CONTROLLER_PUB}\""
echo "    wg_pubkey_saconsole:  \"${SACONSOLE_PUB}\""
echo "    wg_pubkey_target1:    \"${TARGET1_PUB}\""
echo ""
echo "Commit keys.sops.yml to git. The plaintext never touches disk beyond this run."
