# Minutes — 2026-04-04 — Clean rebuild: destroy dev01 + dev02, full uninterrupted UI build

## Attendees
- `<controller>` operator
- Claude (secretary)

## Objective
Destroy both dev VMs and rebuild from UI — prove uninterrupted end-to-end pipeline with #94 fix.

## Pre-flight
- sync_check: 46 passed, 0 failed, 4 warnings (all non-blocking)
- dev01 HTTP 502 (expected — about to destroy)
- uvicorn + Cytoscape UI both responding

## Decisions & Actions

### 1. ce_sri repo fixes verified
- **#83** (modules.txt accent): fixed in commit `c4fb7d3` — already pushed to `wip/2026-03-25`
- **#84** (fixture conflict): fixed in commit `3c287ed` — already pushed to `wip/2026-03-25`
- No action needed — both fixes confirmed on remote

### 2. #94 fix applied (H3/H4a reorder)
- H3 (set-admin-password) moved after H4a (DELETE FROM __Auth + regenerate API key)
- Applied to: `tools/api.py` template, `dev01-differentiate.sh`, `dev02-differentiate.sh`, `dev03-differentiate.sh`
- dev01 also gained missing H4a section
- dev03 migrated from inline heredoc to `h4a_apikeys.py` script call
- `platforms/kvm/CLAUDE.md` updated to reflect new order
- Commit: `2207ccf`

### 3. GitHub issues closed (6 total)
- **#83**: ce_sri modules.txt accent
- **#84**: ce_sri fixture conflict
- **#94**: H4a wipes admin password (auto-closed via commit message)
- **#74**: Externalize production customizations (already complete)
- **#88**: MCP servers not connecting (resolved — `~/.claude.json` not `settings.json`)
- **#26**: bootstrap_targets poll virsh domstate (already implemented)

### 4. Commits pushed
- `4673257` — docs(session): add pending session logs and mission dialog
- `6899b32` — chore(kvm): add dev02 to hosts_map, inventory, and WireGuard keys
- `2207ccf` — fix(kvm): reorder H3 after H4a — fixes #94

### 5. Destroy + rebuild cycle
- dev01 destroyed (job `b8578631`) — clean, WG peer removed, snapshots deleted
- dev02 destroyed (job `f7d1322e`) — clean, WG peer removed, snapshots deleted
- dev01 provisioned (job `a19bc0f4`) — full pipeline ~23 min, snapshot taken
- dev02 provisioned (job `90d2c5a1`) — full pipeline ~25 min, snapshot taken

### 6. Verification
| Check | dev01 | dev02 |
|---|---|---|
| Health (web/app/db) | green/green/green | green/green/green |
| HTTPS | 200 | 200 |
| Admin login (sasa) | 200 | 200 |

**#94 fix confirmed**: admin password survives H4a __Auth wipe on both VMs.

### 7. Post-rebuild commit
- `bccd161` — chore(kvm): regenerate dev01 + dev02 after clean rebuild
- dev01-differentiate.sh now uses Jinja2-rendered templates (inline heredocs eliminated by template engine)

## Observations
- dev01-differentiate.sh shrank from ~390 lines to ~260 lines — the api.py template now renders configs via Jinja2 instead of inline heredocs
- h4e_patch_parms.py multi-line backslash continuations collapse to single line in f-string templates — cosmetic, functionally correct
- DB restore step remains the bottleneck (~12 min per VM)

## Deferred
- GH #87: Refresh secrets gap
- GH #90/#91: Topology UI provisioning state + live logs
- GH #68: Refresh fast path (skip G/H DB restore)
- SRI PRUEBAS retry (2026-04-07)
- GH #50: cf-mcp-refresh not in repo
