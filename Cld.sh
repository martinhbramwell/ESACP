#!/usr/bin/env bash
# Cld.sh — Launch Claude Code with Cloudflare MCP token pre-refreshed
#
# Run this from the ESACP project root instead of calling `claude` directly.
# Ensures the Cloudflare MCP OAuth token is fresh before Claude Code starts,
# preventing the "Cloudflare tools not available" silent failure.
#
# Satellite terminal (ESACP#383): by default Claude Code runs inside a shared
# tmux session ("esacp") so a second terminal — e.g. the Iconia tablet over
# WireGuard — can attach to the SAME live session and drive it:
#     ssh you@10.10.0.2 -t 'tmux attach -t esacp'
# `window-size largest` keeps this terminal full-size when the smaller tablet
# screen attaches. Set ESACP_NO_TMUX=1 to launch claude directly (no mirror).

set -euo pipefail

cd "$(dirname "$0")"

if [[ -f .needs-cf-mcp ]]; then
  cf-mcp-refresh && rm -f .needs-cf-mcp
fi

SESSION="${ESACP_TMUX_SESSION:-esacp}"

# Already inside tmux, or mirroring opted out, or tmux missing → run directly.
if [[ -n "${TMUX:-}" || "${ESACP_NO_TMUX:-0}" == "1" ]] || ! command -v tmux >/dev/null 2>&1; then
  exec claude --chrome
fi

# Attach to an existing shared session, or create one running Claude Code.
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" "claude --chrome"
  tmux set-option -t "$SESSION" window-size largest    # don't shrink to the smallest client (#383)
fi
exec tmux attach -t "$SESSION"
