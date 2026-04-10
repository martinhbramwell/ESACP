#!/bin/bash
# ESACP fallback install for toshiba
# Run as: bash install.sh
# Prereqs: this script installs Node.js (nvm), Claude Code, gh, sops, age,
#          and deploys all config needed to resume ESACP work.
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$HOME/projects/Logichem/ESACP"

echo "=== 1/7: Install nvm + Node.js 18 ==="
if ! command -v node &>/dev/null; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm install 18
    nvm use 18
    echo "  [OK] Node.js $(node --version) installed"
else
    echo "  [SKIP] Node.js already installed: $(node --version)"
fi

echo "=== 2/7: Install Claude Code CLI ==="
if ! command -v claude &>/dev/null; then
    npm install -g @anthropic-ai/claude-code
    echo "  [OK] Claude Code installed"
else
    echo "  [SKIP] Claude Code already installed: $(claude --version)"
fi

echo "=== 3/7: Install gh (GitHub CLI) ==="
if ! command -v gh &>/dev/null; then
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update && sudo apt-get install -y gh
    echo "  [OK] gh installed"
    echo "  NOTE: Run 'gh auth login' after install to authenticate"
else
    echo "  [SKIP] gh already installed: $(gh --version | head -1)"
fi

echo "=== 4/7: Install sops + age ==="
sudo cp "$BUNDLE_DIR/bin/sops" /usr/local/bin/sops
sudo cp "$BUNDLE_DIR/bin/age" /usr/local/bin/age
sudo chmod 755 /usr/local/bin/sops /usr/local/bin/age
echo "  [OK] sops $(sops --version 2>&1 | head -1) + age $(age --version)"

echo "=== 5/7: Deploy SOPS age key ==="
mkdir -p "$HOME/.config/sops/age"
cp "$BUNDLE_DIR/config/sops-age/keys.txt" "$HOME/.config/sops/age/keys.txt"
chmod 600 "$HOME/.config/sops/age/keys.txt"
echo "  [OK] Age key deployed"

echo "=== 6/7: Deploy Claude Code config ==="
# Claude global config
if [ -d "$HOME/.claude" ]; then
    echo "  [WARN] ~/.claude already exists — backing up to ~/.claude.bak"
    mv "$HOME/.claude" "$HOME/.claude.bak"
fi
cp -r "$BUNDLE_DIR/config/dot-claude" "$HOME/.claude"
cp "$BUNDLE_DIR/config/dot-claude.json" "$HOME/.claude.json"
echo "  [OK] Claude config deployed"

# SSH key for VM access
cp "$BUNDLE_DIR/config/ssh/hasan_mighty" "$HOME/.ssh/hasan_mighty"
cp "$BUNDLE_DIR/config/ssh/hasan_mighty.pub" "$HOME/.ssh/hasan_mighty.pub"
chmod 600 "$HOME/.ssh/hasan_mighty"
echo "  [OK] SSH key hasan_mighty deployed"

echo "=== 7/7: Clone ESACP repo + deploy project config ==="
mkdir -p "$HOME/projects/Logichem"
if [ -d "$PROJECT_DIR" ]; then
    echo "  [SKIP] $PROJECT_DIR already exists — pulling latest"
    cd "$PROJECT_DIR" && git pull
else
    cd "$HOME/projects/Logichem"
    git clone git@github.com:martinhbramwell/ESACP.git
    echo "  [OK] ESACP cloned"
fi
# Deploy project-level .claude/
cp -r "$BUNDLE_DIR/config/project-dot-claude" "$PROJECT_DIR/.claude"
echo "  [OK] Project .claude/ deployed"

echo ""
echo "================================================"
echo "  ESACP fallback environment ready on toshiba"
echo "================================================"
echo ""
echo "Remaining manual steps:"
echo "  1. gh auth login"
echo "  2. Add SSH config entries if needed (toshy aliases won't apply — you ARE toshy)"
echo "  3. Claude Code API key: run 'claude' and follow auth prompts"
echo "  4. Delete this bundle: rm -rf $BUNDLE_DIR"
echo ""
