# Minutes — 2026-03-31 Rebuild Pre-requisites Session

## Objective
Fix the 4 pre-requisites for a full dev01 rebuild from template.

## Completed

- ✅ **Playwright installed** — `@playwright/test` + chromium; Inspect test passes (24.9s)
  - Fixed 3 `waitForSelector` bugs: `.hidden` class vs `state: 'hidden'`
  - Playwright section added to `prototypes/cytoscape/CLAUDE.md`
  - Commit: `6b64e66`

- ✅ **GH #75 — Patch log seeding** — dead Section D2 removed from differentiate scripts + api.py template; UPDATE moved to `BaRe/handleRestore.sh` (between restore and migrate)
  - Root cause: Section D2 ran BEFORE DB restore, which overwrites the seeded entry
  - Commits: ESACP `6b64e66`, BaRe `07323d0`

- ✅ **Returnable app TypeError** — not reproducible. `bench migrate` completes on dev01 with all 5 apps (frappe, erpnext, ce_sri, returnable, route_planner). Will confirm during full rebuild.

- ✅ **App rsync in Refresh** — `_run_refresh()` in api.py now rsyncs ce_sri, returnable, route_planner, BaRe before running differentiate.sh
  - Commit: `6b64e66`

- ✅ **GH #76 — AMBIENTE enforcement** — Section B2 added to differentiate.sh: runs `setTESTMODE.sh` + overrides `ERP_HOST` to dev site URL
  - Root cause: `ce_sri_prod` rsync copies production `.env` with `AMBIENTE=2`
  - `setTESTMODE.sh`/`setPRODUCTIONMODE.sh` are the existing switching mechanism — do NOT delete .env variants
  - Commit: `3d2fcbd`

## Decisions

- **Bench dir symlink is correct**: `frappe-bench` (real) ← `frappe-bench-{NICKNAME}` (symlink). Packer creates undifferentiated `frappe-bench`; venv shebangs hardcode that path. User's original ce_sri scripts call `bench init frappe-bench-${A_CODE}` (no rename needed), but Packer trade-off saves ~10 min per deploy. Accepted.
  - Saved to `feedback_bench_dir_symlink.md`

- **Claude in Chrome architecture**: CLI + Chrome extension must be on same machine (local MCP/stdio). Playwright tests only need Node.js + network access. Long-term: Playwright regression suites for ERPNext business use cases.

## Deferred

- 🔄 Full dev01 rebuild from template (primary objective — pre-reqs now met)
- 🔄 Permissions via bench commands (Phase 5)
- 🔄 Dashboard chart recreation (Phase 6)
- 🔄 Custom Translations (Phase 7)
- 🔄 Extended Playwright coverage (fixture verification test)
- 🔄 GH #68 — Refresh fast path
- 🔄 GH #50 — cf-mcp-refresh not in repo
- 🔄 GH #37 — jobs killed on uvicorn restart

## Action Points

- User switching to new LAN — update toshiba IP in `~/.ssh/config` (toshy) and `/etc/wireguard/wg0.conf` (Endpoint)
- Next session: full dev01 rebuild from template, verify fixtures applied automatically
- Push ESACP + BaRe commits after LAN switch confirmed working
