# Minutes — 2026-04-03 09:30 — Jinja2 Template Refactor (GH #89)

## Objective
Extract differentiate.sh heredocs into standalone Jinja2 renderers.

## Outcomes

### ✅ Completed
- Pre-flight sync_check: 45/47 passed, fixed saconsole WG peer key mismatch for dev02
- Destroyed dev02 + dev03 via Playwright topology tests (not needed for this session)
- Created 5 Jinja2 templates: envars.sh, bash_aliases, supervisor conf, nginx vhost, gh_askpass
- Created 2 static files: Procfile, ssh_config
- Created 5 standalone Python renderers with dual CLI + module mode
- Created shared `_base.py` (render_template, load_params, cli_main)
- Refactored api.py Step 12: controller-side rendering + SCP bundle + slimmed f-string
- All rendered outputs verified against dev01 reference
- Fixed #92: backslash-escaped backticks in H4a __Auth SQL (quoted heredoc)
- Committed and pushed: ae035fc, e45429e, 5bfe371

### 🔄 Not achieved
- dev02 deploy failed at H4a: `User [Administrator] not found` after bench restore (#93)
- https://dev02.iridium.blue/ is NOT working

## Issues Filed
- #90 — Topology UI: node shows "Unprovisioned" during active provisioning
- #91 — Topology UI: clicking provisioning node should show live logs
- #92 — H4a __Auth SQL backtick escaping (FIXED, committed)
- #93 — H4a generate_keys: Administrator not found after bench restore (OPEN, blocks deploys)

## Action Points for Next Session
1. Investigate #93: why Administrator user is missing after bench restore + migrate
2. Get https://dev02.iridium.blue/ working end-to-end
3. dev02 is currently half-provisioned on toshiba — destroy and redeploy after fix

## Deferred (unchanged from agenda)
- GH #87: Refresh secrets gap
- dev01 HTTP 502
- SRI PRUEBAS retry (2026-04-07)
