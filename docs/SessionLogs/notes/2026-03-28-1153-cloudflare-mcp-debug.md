# Debug Notes — Cloudflare MCP OAuth Failure
## Session: 2026-03-28 11:53

---

## Symptom

Cloudflare MCP tools never appeared in Claude Code despite the user completing the OAuth
browser flow manually 4+ times across multiple sessions.

## Investigation

1. Confirmed binary path in `settings.json` points to installed binary, not npx — correct.
2. No `~/.mcp-auth/` directory found initially → ran broader search.
3. Found `~/.mcp-auth/mcp-remote-0.1.37/` with valid token files (timestamped 10:46 today).
4. Installed binary version: **0.1.38** — looks for `~/.mcp-auth/mcp-remote-0.1.38/` which did not exist.
5. `getConfigDir()` source confirmed: `~/.mcp-auth/mcp-remote-{version}/` is the path for both 0.1.37 and 0.1.38.

## Root Cause

`mcp-remote` was upgraded from 0.1.37 → 0.1.38 (npm install -g) at 11:26 today — **after**
the last successful manual OAuth cached tokens for 0.1.37 at 10:46. The new version looked
in a non-existent directory, found no tokens, and attempted OAuth. But Claude Code owns the
subprocess stdio — the OAuth browser URL was never shown to the user. The server silently
failed to connect on every Claude Code restart.

## Fix Applied

```bash
mkdir -p ~/.mcp-auth/mcp-remote-0.1.38
cp ~/.mcp-auth/mcp-remote-0.1.37/* ~/.mcp-auth/mcp-remote-0.1.38/
```

Server URL hash (`6244cf5467a6f706b7b55d5e88d4e4c4`) is stable across versions.
Token format is compatible. Refresh token present — access token will auto-renew.

## Token Scopes Confirmed

```
account:read dns_analytics:read dns_records:read dns_records:edit
dns_settings:read offline_access user:read zone:read
```

Sufficient for DNS record management (iridium.blue A records, DDNS updates).

## GH Issue

#49 — opened and closed same session.

## Prevention

See `reference_mcp_remote_tokens.md` in memory. On any future `npm install -g mcp-remote`,
copy the token cache directory to the new version path before restarting Claude Code.
