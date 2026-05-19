# Agenda — Next Session (from 2026-03-31 ce_sri pipeline)

## Primary Objective

### 1. Complete pipeline migration: GitHub clone replaces controller rsync

See `memory/project_github_clone_migration.md` for full state.

**Done:**
- All 4 bespoke app repos synced with production state, pushed to `wip/2026-03-31`
- Deploy keys generated on Mighty (`~/.ssh/you_gh_*`), passphrase in `you_gh.txt`
- Deploy keys registered on GitHub (ce_sri, ce_sri_svc, route_planner)
- stop.py, Procfile, ce_sri_svc supervisor conf all committed (b7d4fa2)

**TODO:**
1. **api.py Step 10**: replace rsync of ce_sri/returnable/route_planner with SCP of deploy keys + passphrase to VM
2. **differentiate.sh**: add SSH config aliases + SSH_ASKPASS + `bench get-app` / `git clone` sections
   - ce_sri: `bench get-app git@ce_sri.gh:martinhbramwell/ce_sri.git --branch wip/2026-03-25`
   - route_planner: `bench get-app git@route_planner.gh:martinhbramwell/route_planner.git --branch wip/2026-03-31`
   - BtlMng (returnable): `bench get-app https://github.com/martinhbramwell/BtlMng.git --branch wip/2026-03-31` (public — no key)
   - ce_sri_svc: `git clone git@ce_sri_svc.gh:martinhbramwell/ce_sri_svc.git --branch wip/2026-03-31` into `apps/ce_sri/services/ce_sri_svc/`
   - BaRe: `git clone https://github.com/martinhbramwell/BaRe.git` (public — no key)
3. **Refresh endpoint**: replace rsync with `git pull` on VM
4. **Full rebuild test**: destroy dev01, deploy from template, verify clone-from-GitHub flow end-to-end
5. Update dev01 + dev02 differentiate scripts

### 2. Verify ce_sri_svc running after rebuild
- `bench start` shows `ce_sri_svc.1` with correct API Server banner
- supervisor mode shows `frappe-bench-ce-sri-svc RUNNING`
- AMBIENTE=1, ERP_HOST=dev01.iridium.blue

## Carried Business

### 3. GH #79 — commit www.js banner change to ce_sri_svc repo
Already on `wip/2026-03-31` branch (commit 413d470). Close issue after rebuild verifies it.

### 4. Original agenda items (deferred)
- Permissions via bench commands (Phase 5)
- Dashboard chart recreation (Phase 6)
- Custom Translations (Phase 7)
- Extend Playwright coverage

### 5. Carried issues
- GH #68 — Refresh fast path
- GH #50 — cf-mcp-refresh not in repo
- GH #37 — api.py jobs killed on uvicorn restart
