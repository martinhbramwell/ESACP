#!/usr/bin/env bash
set -euo pipefail

# Ensure correct Node version (Vite requires >=20.19)
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use

npm run dev

