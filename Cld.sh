#!/usr/bin/env bash
# Cld.sh — Launch Claude Code with Cloudflare MCP token pre-refreshed
#
# Run this from the ESACP project root instead of calling `claude` directly.
# Ensures the Cloudflare MCP OAuth token is fresh before Claude Code starts,
# preventing the "Cloudflare tools not available" silent failure.

set -euo pipefail

cd "$(dirname "$0")"

cf-mcp-refresh

claude --chrome
