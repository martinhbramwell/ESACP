# Session Minutes — #256 wizard-replay race fix + Run 03 green

**Date:** 2026-04-20 15:50–17:10 EDT (approx)
**Branch:** `accept/03-cli-pseudo-wizard`
**PR:** #257 — merged via local GPG-signed merge commit `ad27d48` at 2026-04-20T20:05:01Z
**Issue:** #256 — closed `state=completed` at 2026-04-20T20:05:01Z
**Agenda reference:** the fix scope is driven by #256 directly; Run 03 exit state follows `internal_docs/SessionLogs/acceptance-matrix/03-cli-vm-pseudo-company-wizard-creates-backup.md`.

## Objective

Fix the `page.close()`-vs-`setup_complete`-response race from #256 so that `accept-03-cli-pseudo-wizard.spec.js` runs green end-to-end and the resulting B03 golden backup actually contains the Pseudo-Co Company + Chart of Accounts.

## Outcome — GREEN

- `accept-03` attempt 7: **1 passed (9.8m)**.
- B03 artefact: `platforms/kvm/golden_backups/20260420_142102-dev01_iridium_blue.tgz` (1.30 MB) — 14 `Pseudo-Co` references in the decompressed SQL stream.
- Live canary (post-test): `GET /api/resource/Company/Pseudo-Co` → 200, `default_bank_account="CAD - PSC"`, `creation=2026-04-20 13:04:39`, `modified=2026-04-20 13:05:14`.
- Exit state per Run 03 agenda: dev01 alive with skeletal Pseudo-Co ERPNext, B03 archived on main.

## Fix summary (from PR #257)

**Root cause.** Playwright `.click('Complete Setup')` returns on request dispatch, not on the server-side `setup_wizard.setup_complete` reply. CoA seeding (~30–45s) continued after the original recording's `page.goto('/app') → page.close()`; backup snapshotted pre-seed DB; canary hit 404 on Company/Pseudo-Co.

**Three changes** (`411612e`):

1. `prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js` — replaced the goto+close tail with `Promise.all(page.waitForResponse(setup_complete POST), click)`. Belt-and-braces via `page.evaluate(async () => fetch('/api/resource/Company/Pseudo-Co'))` verifying `default_bank_account` is populated (post-CoA marker). Added Industry-page flake guard: wait for `#freeze.modal-backdrop.in` to clear, Escape-dismiss any lingering `.modal.fade.show`, then `.check()`.
2. `prototypes/cytoscape/tests/accept-03-cli-pseudo-wizard.spec.js` — Step 6 now decompresses the B03 SQL stream and greps for `Pseudo-Co`. Prior check only validated tarball structure.
3. `tools/pipeline/stages/wizard_completion/capture_backup.py` — docstring notes the wizard-side gate is authoritative (initial controller-side attempt via urllib session hit HTTP 403 on `frappe.client.get_single_value`; removed).

## What the 7 attempts looked like

| # | Trigger | Result | Takeaway |
|---|---|---|---|
| 1 | #256 filing (prior session) | canary 404 | Race surfaced |
| 2 | `waitForFunction(async)` + urllib gate | gate 403 | Gate broken; wizard gate spuriously green |
| 3 | gate removed | Manufacturing checkbox blocked 30s | Modal flake surfaced |
| 4 | re-run | canary 404 | `waitForFunction(async)` returned truthy prematurely |
| 5 | `Promise.all(waitForResponse, click)` + page.request | Manufacturing checkbox blocked | Flake recurred |
| 6 | +flake guard | `page.request.get` Invalid URL | Path-only URL rejected |
| 7 | `page.evaluate(fetch)` | **GREEN (9.8m)** | Shipped |

## Deviation from #256's suggested fix direction

Issue proposed `page.waitForFunction(() => frappe.boot.setup_complete === 1)` or polling Company count. Both are flavours of the async-predicate pattern that attempt 4 proved unreliable. `Promise.all(waitForResponse, click)` is deterministic because it doesn't rely on polling — the response callback fires when the HTTP response arrives. Documented on the issue (comment `#issuecomment-4283935639`).

## Memory updated

`memory/feedback_playwright_async_predicate.md` — new feedback memory capturing the `page.waitForFunction(async fn)` gotcha. Indexed in MEMORY.md next to the existing Playwright entry.

## Open concerns not addressed this session

- **Bootstrap welcome modal root cause.** Flake guard works but the modal's origin wasn't investigated. May be an ERPNext industry-page tour dialog. If it recurs with a different structure, the Escape-dismiss may not catch it.
- **Controller-side defence-in-depth.** Removed after HTTP 403; not re-implemented via SSH+bench. Future wizard recordings that omit the `waitForResponse` pattern will race silently.
- **sync_check failures** (dev02, dev03, target5 unreachable) at session start — not investigated; same #247 pattern the test already swallows.

## Next

Run 03 is green; matrix unblocked for whatever Run comes next (04 = UI dev VM from backup, per transport-parity plan).
