# Session Minutes — 2026-04-15 07:00

**Objective:** End-to-end test Generic ERPNext template (#158) — all three wizard completion paths

**Branch:** `feat/158-generic-erpnext-template`

---

## Completed

### Step 1: "Use existing" path — PASS
- Stopped dev01 via topology UI to free RAM
- Deployed target5 via Generic ERPNext template with `wizard_mode=existing` and golden backup `20260409_080145-generic_iridium_blue.tgz`
- Pipeline completed all 9 stages in ~10 minutes
- ERPNext live at https://target5.iridium.blue with "Demo Co" configuration
- **Bug found:** Ansible `hub_key` undefined at parse time (#179) — WireGuard setup skipped
- **Bug found:** target5 showed `provisioned=false` — snapshot name "Wizard Ready" doesn't contain "Baseline" (#180)

### Step 2: "Record" path — PASS
- Destroyed target5, redeployed with `wizard_mode=record`
- Pipeline completed stages 1-9, then Playwright codegen opened headed browser
- User completed ERPNext setup wizard manually (Canada, Manufacturing+Retail, Demo Co., Standard with Numbers)
- Recording saved: `recordings/wizard/target5-20260415_113221.spec.js` (4.4 KB)
- Golden backup captured: `20260415_064224-target5_iridium_blue.tgz` (1.3 MB)

### Step 3: "Replay" path — PASS (after fixes)
- Destroyed target5, redeployed with `wizard_mode=replay`
- **Replay infrastructure had 3 bugs:**
  1. Temp config written to `/tmp/` — Node couldn't resolve `@playwright/test` (fixed: write in project tree)
  2. `replay_wizard.js` used `@playwright/test` runner but codegen produces raw standalone scripts (fixed: rewrote to execute via `node` directly with `.cjs` extension and `PLAYWRIGHT_BROWSERS_PATH`)
  3. Raw recording had duplicate Login button action causing headless timeout (fixed: removed duplicate, added `waitForURL`)
- After fixes, reverted target5 to "Wizard Ready" snapshot and ran replay
- Replay completed successfully — ERPNext configured with same wizard values (Demo Co., Canada, Manufacturing)

### Observability stack investigation
- sync_check reported all 8 containers down — false positive
- Root cause: SSH config for saconsole uses unroutable `HostName saconsole` with no ProxyJump
- Containers all healthy when reached via WireGuard IP (10.10.0.1)
- Stale host key cleared from known_hosts

### GitHub comment on #138
- Suspicious comment from `ericjoye` — AI-generated drive-by contribution attempt
- Recommended: don't engage, don't grant access

## Bugs Filed

| Issue | Title |
|---|---|
| #178 | SSH config for saconsole uses unroutable hostname — sync_check reports all containers down |
| #179 | Ansible Play 2/3 `hosts: "{{ hub_key }}"` fails — variable undefined at parse time |
| #180 | Generic provision snapshot name missing "Baseline" — shows unprovisioned |
| #181 | Re-write Playwright recording: 1) cleaned up 2) parameterised |

## Code Changes

- `prototypes/cytoscape/recordings/replay_wizard.js` — complete rewrite: executes raw codegen scripts via node (not @playwright/test runner), resolves browser path from `~/.cache/ms-playwright`
- `prototypes/cytoscape/recordings/wizard/target5-20260415_113221.spec.js` — removed duplicate Login action, added `waitForURL`

## Not Done

- Step 4: Playwright acceptance tests (`generic-template.spec.js`) — deferred
- Step 5: PR and merge — deferred (Step 4 prerequisite)
- PR #170 (fix #168) — not reviewed
- saconsole rebuild with current codebase (#178 full scope) — separate session
- Form submission bug (deploy dialog hostname/nickname fields appear filled but are empty in DOM) — needs investigation
