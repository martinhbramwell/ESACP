#!/usr/bin/env bash
set -euo pipefail

VITE_PORT=5173

# Bail out if Vite is already running on the expected port
if lsof -i :"${VITE_PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Vite already running on port ${VITE_PORT} — not starting another instance."
    exit 0
fi

# Ensure correct Node version (Vite requires >=20.19)
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use

npm run dev

