# Acceptance Matrix — Transport Parity Close-out

**Matrix closed: 2026-04-21.** Seven runs signed off; the pre-ERPNext-v16 foundation is live-verified across CLI and UI transports.

Plan: `~/.claude/plans/acceptance-matrix-transport-parity.md`

## Run log

| Run | Transport | Variant | Result | Runtime | Merge commit | PR | Minutes |
|---|---|---|---|---|---|---|---|
| 01 | CLI | saconsole rebuild | ✅ | live-verified | `48b7226` (#231 fix) | #232 | 2026-04-19 |
| 02 | CLI | full company-specific from backup | ✅ | 27.7m | `aa69022` | #251 | 2026-04-20-0948 |
| 03 | CLI | pseudo-company wizard creates backup (B03) | ✅ | 9.8m | `ad27d48` | #257 | 2026-04-20-1550 |
| 04 | CLI | pseudo-company restore from B03 | ✅ | 11.1m | `33c4a3d` | #258 | 2026-04-20-1800 |
| 05 | UI | full company-specific from backup | ✅ | 30.4m | `9124505` | #266 | 2026-04-21-0812 |
| 06 | UI | pseudo-company wizard creates backup (B06) | ✅ | 10.6m | `29aec7a` | #272 | 2026-04-21-1256 |
| 07 | UI | pseudo-company restore from B06 | ✅ | 12.0m | `5350641` | #273 | this session |

CLI 4/4 + UI 3/3 = **7/7**. Run 01 has no UI parity partner by design — saconsole lifecycle is CLI-only (see `memory/feedback_saconsole_cli_only.md`).

## Parity results

### Run 02 ↔ Run 05 — full company-specific from golden production backup

- Same restore source (golden production `.tgz`), same pipeline (`provision_mode=restored`, stages 1–9).
- Both green on `login as Administrator + GET /api/resource/Item/Test%20Item + /app/item/Test%20Item` canary.
- **Transport asymmetry noted (non-blocker, tracked in #235):** UI forces `vm_role: dev:unspecified` (main.js:1828) whereas Run 02 CLI set `dev:full_company_specific`. Acceptance did not assert `vm_role` — canary is the parity gate.
- **Runtime gap (non-blocker):** CLI 27.7m vs UI 30.4m. Both dominated by restore + post-restore cold-start; UI adds Deploy-dialog overhead + #265 form-parser fix.

### Run 03 ↔ Run 06 — pseudo-company wizard creates backup

- Same wizard recording (`pseudo-co-wizard.spec.js`) replayed both times. B03 (Run 03) and B06 (Run 06) are content-equivalent — **14 Pseudo-Co hits in each** (verified via `tar -xzOf | grep -c`).
- Both canaries pass the same four-field assertion: `Pseudo-Co` / `PSC` / `CAD` / `Canada` + `Company.count=1`.
- Run 03 took 9.8m, Run 06 took 10.6m — sub-second delta after the #267 modal-race fix (PR #270 `af05f80`) and #268 terminal-error-state fix (PR #269 `3499447`).
- **Structural findings surfaced during runs:** #256 (wizard `page.close()` race — fixed via `Promise.all(waitForResponse, click)`), #267 (modal-during-click race — fixed via DOM-mutation checkbox force), #268 (`waitForJob` ignored `'error'` state — fixed via throw).

### Run 04 ↔ Run 07 — pseudo-company restore from wizard backup

- Run 04 consumed B03, Run 07 consumed B06. Both are `existing` mode (`wizard_mode=existing`, no wizard replay, no new backup captured).
- **Canary facts identical:** `Pseudo-Co` / `PSC` / `CAD` / `Canada` + `Company.count=1` — byte-for-byte match.
- **Golden-backups delta = 0 in both runs** — restore correctly re-uses its source without duplicating it.
- Run 04 took 11.1m, Run 07 took 12.0m — 54s delta attributable to UI form-fill overhead + slightly slower `handleRestore.sh` stage on this run (provision job 638s vs Run 04's 596s).

## Transport-parity verdict

All three parity pairs produce **functionally indistinguishable endpoints**. Same ERPNext state, same canary hits, same backup artefact when one is produced, same sync_check row. The UI and CLI dispatch to the same pipeline primitives (Gen 3 refactor completion, PR #215) — Runs 05/06/07 are the live proof that this abstraction holds under the full provision → wizard → restore lifecycle, not just integration-test mocks.

## Issues filed during the matrix

All blockers were fixed and closed during the matrix; a few latent/tracker issues remain open:

**Closed during matrix:**
- #231 — cloud-init race in saconsole bootstrap (pre-Run 01)
- #233 — `addHost` CLI subcommand missing (blocked Run 02)
- #234 — `provisionGeneric` CLI subcommand missing (blocked Run 03)
- #239 — real client name scrub (SHELVED Run 02 attempt 3, three-commit fix)
- #247, #248, #249 — Run 02 attempt-4 halt fixes (sync_check throw / logo / Cytoscape race)
- #253, #256, #259, #260, #262, #265, #267, #268 — wizard, parser, dormant-VM, agenda, 1:1:1-amendment, UI form, modal, job-state fixes

**Open after matrix close (none block ERPNext work):**
- #271 — `accept-NN` destroy-guard flake on pre-registered-only entry state (latent; surfaced in Run 06 attempt 2). Fix audit should cover accept-02..05.
- #235 — 13 CLI/API transport asymmetries (tracker, non-blocking).
- #250 — company logo [SKIP] on generic provisions (wizard-path branding gap; UI-path restore covers it).
- #219, #220 — main.js / bootstrap_hub.sh decomposition (parked post-matrix).

## Reminders for the next session(s)

- Untracked `doCytoscape.sh` / `doVite.sh` — unresolved since 2026-04-21-1033. Decide commit vs `.gitignore` vs leave. Interacts with #244 (`*.tgz` in `.gitignore`).
- Dev01 sync-check "unreachable" carve-out — still not filed as an issue. dev01 exit state of the matrix is **running** (Run 07 left it restored), so sync_check is green — but the concern returns whenever a test leaves dev01 destroyed.
- #271 fix session should audit accept-02..05 specs for the same destroy-guard gap.

## What the matrix unblocks

With transport parity live-verified, the next stage of work no longer needs to treat CLI and UI as separate risks. ERPNext-v16 upgrade work, Playwright regression of production workflows, and CloudStack backend expansion can all proceed against either transport with equal confidence. MEMORY.md flags the foundation-solid status; subsequent ERPNext-focused sessions can start from this baseline.

## Erratum — 2026-04-23 — bench-layer contamination in "generic" runs

Runs 03, 04, 06, 07 (pseudo-company variant) treated the provisioned
substrate as "generic" for comparison purposes. **That claim holds at the
site and database layers** — `sites/apps.txt`, `sites/apps.json`, and
`bench --site ... list-apps` all show `frappe` + `erpnext` only.

It does **not** hold at the bench layer. Until the fix in #289 lands,
Stage 6 provisioned `apps/ce_sri`, `apps/route_planner`, `apps/returnable`,
and `apps/ce_sri/services/ce_sri_svc` unconditionally, patched the
Procfile with `ce_sri_svc`, and deployed the ce_sri deploy-key set
regardless of `provision_mode`. The matrix's CLI↔UI parity verdicts are
**unaffected** — both sides ran against the same contaminated substrate,
so the pairs remain apples-to-apples — but the word "generic" in those
runs meant *site-level-only* generic, not *bench-level* generic.

#289 (Stage 6 gate on `provision_mode="generic"`) is the first
sub-branch of `umbrella/ladder-fixture` and closes this gap. Future
"generic" runs will produce a clean bench layer (`frappe`, `erpnext`,
`BaRe` only; no ce_sri/route_planner/returnable; no ce_sri_svc
Procfile/supervisor/npm; no you_gh_* deploy keys; envars at
`/opt/generic/envars.sh`).
