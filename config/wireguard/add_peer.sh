#!/usr/bin/env bash
# add_peer.sh — Add a new WireGuard peer to the existing keys.sops.yml
#
# Use this when keys.sops.yml already exists (keys were previously generated)
# and you need to add one new peer without regenerating all keys.
#
# Usage (from project root):
#   bash config/wireguard/add_peer.sh <peer-name>
#   bash config/wireguard/add_peer.sh target2
#
# Output: updates keys.sops.yml in place; prints the public key line to paste
#         into ansible/group_vars/all.yml.
#
# Prerequisites: wg, sops, age key at ~/.config/sops/age/keys.txt, python3+pyyaml

set -euo pipefail

PEER="${1:-}"
if [[ -z "${PEER}" ]]; then
    echo "Usage: $0 <peer-name>"
    echo "Example: $0 target2"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
KEYS_FILE="${SCRIPT_DIR}/keys.sops.yml"
SOPS_CONF="${PROJ_ROOT}/.sops.yaml"

# ── Preflight ─────────────────────────────────────────────────────────────────

if [[ ! -f "${KEYS_FILE}" ]]; then
    echo "ERROR: ${KEYS_FILE} not found. Run generate_keys.sh first."
    exit 1
fi

for cmd in wg sops python3; do
    if ! command -v "${cmd}" &>/dev/null; then
        echo "ERROR: '${cmd}' not found. Install it and retry."
        exit 1
    fi
done

if [[ ! -f "${SOPS_CONF}" ]]; then
    echo "ERROR: ${SOPS_CONF} not found."
    exit 1
fi

AGE_RECIPIENT=$(grep -oP 'age1[a-z0-9]+' "${SOPS_CONF}" | head -1)
if [[ -z "${AGE_RECIPIENT}" ]]; then
    echo "ERROR: No age recipient found in ${SOPS_CONF}."
    exit 1
fi

# ── Generate new peer's keys ──────────────────────────────────────────────────

echo "Generating WireGuard keypair and PSK for '${PEER}'..."

PEER_PRIV=$(wg genkey)
PEER_PUB=$(echo "${PEER_PRIV}" | wg pubkey)
PEER_PSK=$(wg genpsk)

# ── Decrypt, merge, re-encrypt ────────────────────────────────────────────────
# Private keys are passed via environment variables (not argv) to avoid
# exposure in `ps` output.

WORK_DIR=$(mktemp -d)
trap 'find "${WORK_DIR}" -type f -exec shred -u {} \; 2>/dev/null; rm -rf "${WORK_DIR}"' EXIT

PLAIN="${WORK_DIR}/keys.sops.yml"

echo "Decrypting keys.sops.yml..."
sops -d "${KEYS_FILE}" > "${PLAIN}"

PEER_PRIV="${PEER_PRIV}" \
PEER_PUB="${PEER_PUB}"   \
PEER_PSK="${PEER_PSK}"   \
PEER_NAME="${PEER}"      \
PLAIN_FILE="${PLAIN}"    \
python3 <<'PYEOF'
import os, sys, yaml

peer      = os.environ['PEER_NAME']
priv_key  = os.environ['PEER_PRIV']
pub_key   = os.environ['PEER_PUB']
psk       = os.environ['PEER_PSK']
plain     = os.environ['PLAIN_FILE']

with open(plain) as f:
    data = yaml.safe_load(f)

if peer in data:
    print(f"ERROR: '{peer}' already exists in keys.sops.yml", file=sys.stderr)
    sys.exit(1)

# Insert peer before preshared_keys to keep the file ordered
psks = data.pop('preshared_keys', {})
data[peer] = {'private_key': priv_key, 'public_key': pub_key}
psks[f'{peer}_saconsole'] = psk
data['preshared_keys'] = psks

with open(plain, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
PYEOF

echo "Re-encrypting..."
sops --encrypt \
     --age "${AGE_RECIPIENT}" \
     --input-type yaml \
     --output-type yaml \
     "${PLAIN}" > "${KEYS_FILE}.tmp" && mv "${KEYS_FILE}.tmp" "${KEYS_FILE}"

# Plaintext file is shredded by the trap on exit.

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "✅  '${PEER}' added to config/wireguard/keys.sops.yml"
echo ""
echo "Paste into ansible/group_vars/all.yml:"
echo ""
echo "    wg_pubkey_${PEER}: \"${PEER_PUB}\""
echo ""
echo "Then commit keys.sops.yml and all.yml."
