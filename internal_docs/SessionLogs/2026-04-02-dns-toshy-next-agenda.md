# Agenda — 2026-04-02 — toshy.iridium.blue DNS

## Primary Objective

### Create `toshy.iridium.blue` Cloudflare DNS record and replace hardcoded IP

Replace all references to `192.168.40.16` (toshiba LAN IP) with `toshy.iridium.blue`.
One DNS update instead of hunting hardcoded IPs across sessions.

## Steps

1. **Create Cloudflare A record**: `toshy.iridium.blue` -> `192.168.1.79` (DNS only, no proxy)
   - NOTE: Last session said `192.168.1.79` — verify this is the correct current LAN IP before creating the record
   - Use Cloudflare MCP (should now work — GH #88 fix applied: mcpServers moved to `~/.claude.json`)

2. **Update 6 repo files** that hardcode `192.168.40.16`:
   - `platforms/kvm/CLAUDE.md`
   - `ansible/CLAUDE.md`
   - `ansible/site-kvm.yml`
   - `platforms/kvm/prepare_hypervisor.sh`
   - `docs/PrepareHypervisor.md`
   - `platforms/kvm/bootstrap_saconsole.sh`

3. **Update 2 memory files**:
   - `memory/MEMORY.md`
   - `memory/toshiba_environment.md`

4. **Verify**: `sync_check.sh` still passes after the change; WireGuard resolves hostname at connect time.

## Pre-session check

- Confirm Cloudflare MCP tools appear in `/mcp` (GH #88 fix)
- If still broken, escalate #88 before proceeding
