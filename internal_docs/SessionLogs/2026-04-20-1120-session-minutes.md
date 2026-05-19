# Session Minutes — 2026-04-20 11:20 EDT — Matrix Run 03 attempt 1 (HALTED, #256 filed)

**Branch:** `accept/03-cli-pseudo-wizard` — commit `0673a08` preserved on branch for next attempt
**PR:** none (acceptance fails; do not merge until #256 resolves)
**Issue filed:** [#256](https://github.com/martinhbramwell/ESACP/issues/256) — wizard recording races server-side "Complete Setup" → B03 missing new-company rows + accept-03 canary false-404

---

## Objective (entering)

Execute Matrix Run 03 per agenda `internal_docs/SessionLogs/acceptance-matrix/03-cli-vm-pseudo-company-wizard-creates-backup.md`: CLI-driven skeletal ERPNext on dev01 via Pseudo-Co setup wizard, B03 golden backup archived, UI converges.

## Status

**HALTED at canary per agenda findings protocol.** Root cause isolated, evidence captured, issue filed. dev01 destroyed; tainted B03 deleted; branch preserved for #256-fix session.

---

## What ran

| Phase | Result | Notes |
|---|---|---|
| Self-check (sops + sync_check + API :8088 + Vite :5173 + toshiba SSH + wizard recording stat) | ✅ | All six harness assumptions validated before SUT spend |
| Baseline (dev01 absent) | ✅ | No destroy needed |
| `addHost dev01 --zone development --vm-role dev:pseudo_wizard --hypervisor toshiba` | ✅ | wg_ip=10.10.0.16, virbr0_ip=192.168.122.26 |
| `provisionGeneric dev01 --wizard-mode replay --wizard-arg pseudo-co-wizard.spec.js` | ✅ exit 0 | 475s end-to-end; stages 1-9 + wizard replay + `capture_golden_backup` |
| UI convergence | ✅ | 1s (sub-poll) |
| Canary: `GET /api/resource/Company/Pseudo-Co` | ❌ | HTTP 404 |

## Root cause (confirmed, not inferred)

`prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js` clicks **Complete Setup** then immediately `page.goto('/app') + page.close()`. Playwright's `.click()` dispatches the request and returns — it does **not** wait for Frappe's `setup_wizard.setup_complete` server-side flow (Chart of Accounts seeding etc., ~38s) to finish.

Timeline from on-disk evidence:

| T (UTC)     | Event                                                                 |
|-------------|-----------------------------------------------------------------------|
| 10:40:05    | `handleBackup.sh` snapshots DB → `20260420_104005-dev01_iridium_blue.tgz` |
| 10:40:11.648 | Frappe finishes `INSERT INTO \`tabCompany\`` (Pseudo-Co `creation`)   |
| 10:40:49.122 | Chart of Accounts done (Pseudo-Co `modified`)                         |
| ~10:40:06   | provisionGeneric exits → accept-03 canary fires → 404                 |

Verifications:
- **B03 .sql.gz:** `zcat 20260420_104005*.sql.gz | grep -c Pseudo-Co` → **0**. Zero `tabCompany` INSERT rows for Pseudo-Co.
- **Live dev01 (minutes later):** `/api/resource/Company/Pseudo-Co` → 200, name=Pseudo-Co, abbr=PSC, default_currency=CAD, country=Canada. `get_count?doctype=Company` → `{"message":1}`. Wizard *did* complete; backup+canary simply raced it.

## Scope — not Run-03-specific

Same race is structural in the wizard-completion pipeline: every `record`/`replay` wizard run calls `capture_golden_backup` immediately after browser close. Reference recording `target5-20260415_113221.spec.js` has the same tail; its "working" backup likely succeeded by timing accident. Run 06 (UI pseudo-wizard) would reuse this recording and hit the same race.

Fix direction in #256 (not prescriptive): make the wizard recording await a reliable post-completion signal before `page.close()`, and/or harden `capture_golden_backup` to verify `setup_complete == 1` + expected-company-row-present server-side before running `handleBackup.sh`.

---

## Decisions recorded

| D | Question | Answer |
|---|---|---|
| D1 | Honor agenda's `provision --params` literally, or map to the actual CLI? | **Map to actual.** Agenda's `--params` predates `provisionGeneric` (PR #255). Replaced with `provisionGeneric dev01 --wizard-mode replay --wizard-arg pseudo-co-wizard.spec.js`. Deviation called out in the commit body. |
| D2 | B03 output path — honor agenda's `internal_docs/SessionLogs/.../artefacts/B03-wizard.sql.gz`, or accept current tooling's `platforms/kvm/golden_backups/<ts>-generic_<zone>.tgz`? | **Accept current tooling.** The `.tgz` IS B03. Location/format mismatch flagged in commit body. |
| D3 | Wizard recording design — hand-author codegen-style script, or generate via `npx playwright codegen`? | **Hand-author**, modeled on `target5-20260415_113221.spec.js`. Reason: codegen is an interactive headed process not suited for an automated session; the recording is simple enough to write by inspection. |
| D4 | On canary failure — fix-in-place, or halt + issue? | **Halt + issue** per agenda findings protocol and CLAUDE.md "root cause over symptoms." Even though the fix is one-line (add a post-completion wait), this is the wizard-automation surface the agenda specifically flagged for halting. |
| D5 | dev01 disposition | Destroy. Clean slate for next attempt; next attempt will `destroy-as-precondition` anyway. |
| D6 | Tainted B03 `.tgz` on disk | Delete. Evidence captured in #256 body (0 `Pseudo-Co` occurrences); retaining the file adds no signal. |
| D7 | Branch disposition | **Preserve** `accept/03-cli-pseudo-wizard @ 0673a08`. Spec + recording + params are correct; only the recording's tail needs a wait-for-completion. #256-fix session appends to this branch. |
| D8 | SOPS `keys.sops.yml` ciphertext rotation after destroy | Discard. "Not a perfection project" — equivalent-content ciphertext drift is out of scope, matches earlier pre-Run-03 queue decisions. |

---

## Commits on this branch

| SHA | Title |
|---|---|
| `0673a08` | `test(accept-matrix): Run 03 pseudo-wizard spec + recording + params` |

Files added:
- `internal_docs/SessionLogs/acceptance-matrix/params/03-cli-pseudo-wizard.yml`
- `prototypes/cytoscape/recordings/wizard/pseudo-co-wizard.spec.js`
- `prototypes/cytoscape/tests/accept-03-cli-pseudo-wizard.spec.js`

All three files are correct and do not require changes on top of `0673a08` except the recording's tail (wait-for-completion in the #256 fix).

---

## Exit state

- `main` at `b5ba299` (unchanged this session).
- `accept/03-cli-pseudo-wizard` at `0673a08` (preserved).
- dev01 fully destroyed (all 8 teardown steps OK).
- `platforms/kvm/golden_backups/` back to 2 files (pre-session baseline).
- Working tree clean on branch.
- #256 OPEN, blocks Matrix Run 03 completion.
- Run 03 attempt 2 will begin from this branch with a recording-fix commit on top.

## Follow-ups

- **#256** — wizard recording race fix. Required before Run 03 attempt 2.
- No new issues observed beyond #256. Run 02 canary hardening (sops-derived Admin pwd, destroy-as-precondition, #247/#248/#249 fixes) carried forward into accept-03 and worked as designed.
