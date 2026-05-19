# Session Minutes — 2026-04-20 09:48 EDT — Matrix Run 02, attempt 6 — GREEN

**Branch:** `accept/02-cli-full-company-specific` → merged to `main` as `aa69022`
**PR:** [#251](https://github.com/martinhbramwell/ESACP/pull/251) (MERGED 2026-04-20T13:48:17Z)
**Plan:** `~/.claude/plans/acceptance-matrix-transport-parity.md`

---

## Objective (entering)

Deliver a green Matrix Run 02 — CLI-driven dev VM build with full company-specific ERPNext restored from the golden production backup — by resolving the #247 test-code blocker carried over from attempt 4, plus the user's extended scope:

1. Keep repeating Run 02 until green.
2. Fold destroy into Run 02 (idempotent re-runs).
3. Fix #247 (sync_check execSync bug).
4. Fix #248 (scrub-regression residuals).
5. Tighten budget to 3000s.
6. Document the lab Administrator password pattern without naming the production value.
7. Add a test self-check that validates harness assumptions before SUT spend.

## Status

**GREEN on attempt 6.** PR #251 merged; #247, #248, #249 all closed with state_reason `completed`. One side-finding (#250) filed for a pre-existing logo file-placement gap exposed but not caused by this work.

---

## Decisions recorded

| D | Question | Answer |
|---|---|---|
| D1 | Self-check scope — validate sops decryptability of `build_secrets.sops.yml`? | Yes |
| D2 | Administrator pwd — auto-derive from `build_secrets.sops.yml`, or keep env var? | Auto-derive; operator no longer supplies `ERP_ADMIN_PWD` |
| D3 | Scrub scope — rewrite stored `company_logo` ciphertext too? | Yes — stored value rewritten |
| D4 | PR merge strategy | Local `git merge --no-ff -S` to guarantee GPG-signed merge commit |
| D5 | `#250` scope after user correction (logo IS visible on dev01) | Reframed as "inert upload path; DB restore supplies branding on restored path; revisit with Run 03/06 generic-path" — kept open as pre-existing bug |

---

## Commits on this branch

| SHA | Title | Closes |
|---|---|---|
| `750d97f` | fix(matrix-tests): harden accept-02 + tolerate sync_check.sh non-zero exit | #247 |
| `c4f1ee7` | fix(scrub): rewrite company_logo filename in encrypted ce_sri parms | #248 |
| `c8e289d` | fix(matrix-tests): reload graph after destroy-as-precondition | #249 |
| `aa69022` | Merge pull request #251 (merge commit on main) | auto-closed #247 #248 #249 |

## Changes shipped

- **accept-02 spec** (`prototypes/cytoscape/tests/accept-02-cli-full-company-specific.spec.js`): full restructure —
  - Step 0: self-check preamble (sops decrypt, sync_check parse, API/Vite reachability, hypervisor SSH) — fails fast before 30-min provision spend.
  - Step 1: baseline + destroy-as-precondition (idempotent re-runs, with `page.reload()` to rehydrate Cytoscape).
  - Auto-derived `ERP_ADMIN_PWD` from `build_secrets.sops.yml`.
  - Steps 2–5 unchanged in behavior; Step 6 sync_check wrapped in try/catch.
- **accept-01 spec**: latent #247 pattern fixed surgically (try/catch around `sync_check.sh` execSync).
- **params/02-cli-full-company-specific.yml**: `wait_budget_seconds 3600 → 3000`; header comment pointing to the new lab-admin-password memory.
- **config/ce_sri_parms.sops.json**: encrypted `company_logo` rewritten (via `sops set`).
- **Local (not tracked)**: `__pycache__` cleared under `tools/`.
- **Auto-memory**: `feedback_lab_admin_password.md` added; `MEMORY.md` pointer inserted.

---

## Execution timeline

### Attempt 5 (pre-fix dry run — skipped)
Folded directly into attempt 6 since the #247/#248/#249 fixes were prepared as a single PR rather than iterated independently.

### Attempt 6a — first run after #247 + #248 fix pushed
- Self-check ✅
- Baseline: dev01 present (attempt-4 leftover) → destroy triggered.
- Destroy: all 8 steps ✅ ("Destroy complete — dev01 fully removed.")
- **Cytoscape baseline check ❌ at 49.5s**: `onGraphAtBaseline = true` despite API confirming absence. Root cause: `_refreshVmState()` 30s poll tick had not fired yet; in-memory graph was stale. New issue **#249** filed immediately, fix committed `c8e289d`.

### Attempt 6b — after #249 fix pushed
- 27 min 42 s total wall time (vs empirical ~29 min baseline).
- Self-check ✅
- Baseline: dev01 absent (previous attempt's destroy cleaned it) → no destroy needed.
- addHost ✅
- Provision ✅ — 1615 s (26.9 min).
- Topology convergence ✅ — 1 s.
- Canary ✅ — login as Administrator (pwd derived from sops), REST `Item/Test Item`, desk `/app/item/Test%20Item` renders.
- sync_check row assertion ✅ — `✅ ERPNext dev01 (https://dev01.iridium.blue) — HTTP 200` found despite exit-non-zero from unrelated idle-VM ping failures.
- **1 passed (27.7 m).**

---

## Path decision

Direct to PR + merge per approved D5. Local GPG-signed merge commit, branch retained per `feedback_keep_merged_branches.md`.

---

## Issues filed this session

| # | Title | Role |
|---|---|---|
| **#249** | bug(matrix-tests): accept-02 destroy-as-precondition — Cytoscape graph stale after destroy | Attempt-6a regression; CLOSED via `c8e289d` + PR #251 |
| **#250** | bug(pipeline): company logo [SKIP] on all provisions — upload path inert, file-placement gap | Pre-existing; reframed after user correction (logo IS visible on dev01 — DB restore supplies it). Open. |

## Issues closed this session

| # | Title | Closed via |
|---|---|---|
| **#247** | bug(matrix-tests): execSync of sync_check.sh in Run 01/02 specs throws on script's legitimate non-zero exit | `750d97f` → PR #251 merge `aa69022` |
| **#248** | bug(scrub): #239 completeness — LogichemLogo.png filename still referenced; stale .pyc bytecode | `c4f1ee7` → PR #251 merge `aa69022` |
| **#249** | bug(matrix-tests): accept-02 destroy-as-precondition — Cytoscape graph stale after destroy | `c8e289d` → PR #251 merge `aa69022` |

---

## Findings NOT filed (with reason)

- **Post-destroy residual drift on `config/wireguard/keys.sops.yml` + `hosts_map.yml`.** After `destroy dev01`, `keys.sops.yml` showed rotated ciphertexts for unchanged plaintext (normal sops re-encrypt behavior on file edit) and `hosts_map.yml` gained a trailing blank line. Reverted locally; did not file. Note for future reference: post-destroy trees may need `git checkout --` on these two files; value is nil.

---

## State at session close

- `main` at `aa69022` (merge commit). Branch `accept/02-cli-full-company-specific` retained per `feedback_keep_merged_branches.md`.
- dev01 **destroyed**, working tree clean on `main`.
- Matrix Run 02 status transitions: HALTED attempt 4 → GREEN attempt 6.
- Empirical wall-time budget confirmed: 27–29 min per attempt (budget of 3000 s allows ~2× headroom).

## What unblocks Run 03

1. **#234** — `provisionGeneric` CLI subcommand must be implemented before Run 03 can begin. Open.
2. New session on a new branch off `main` (per 1:1:1 discipline) — e.g., `feat/234-cli-provision-generic` for #234 itself, then `accept/03-cli-pseudo-company-wizard-backup` for Run 03 proper.
3. Agenda file `internal_docs/SessionLogs/acceptance-matrix/03-cli-vm-pseudo-company-wizard-creates-backup.md` remains frozen (#246 deferred).

---

## Session-close audit

### Step 1 — forward-tense resolution

| Phrase | Resolution |
|---|---|
| "I'll report when it finishes" (run kickoff) | Tool call: Bash `run_in_background`; completion notification handled; green reported |
| "Will check when run finishes" (relaunch) | Same pattern as above |
| "I'll still ask for approval after you confirm presence" | Scrapped by user mid-turn; `feedback_keyboard_confirm_before_commit.md` created then deleted; MEMORY.md pointer rolled back |
| "I'll refine the memory" | Scrapped with same roll-back |
| "I'll drop the verification `ls` going forward" | Durable home: `memory/feedback_no_verification_ls_after_rm.md` + MEMORY.md pointer |
| "Run 03 blocker: #234" | Durable home: this minutes file's "What unblocks Run 03" section + MEMORY.md Run 02 tracker |

### Step 2 — GH issues, comment audit

| Issue | New findings this session | Posted to GH? |
|---|---|---|
| #247 | Root-cause confirmed reproducible; fix in `750d97f` | Commit message + PR #251 body; issue auto-closed on merge |
| #248 | SOPS rewrite closes scrub-regression scope; SKIP persists for pre-existing reasons | Commit message `c4f1ee7` + PR #251 body; issue auto-closed on merge |
| #249 | Filed this session; fix in `c8e289d` | Issue body + commit message + PR #251 body |
| #250 | Filed this session; reframed after user correction (logo IS visible on restored-path) | Body edited + audit-trail comment posted as `issues/250#issuecomment-4281410198` |
| #234 | No new findings — referenced only as pre-existing Run 03 blocker | N/A |
| #239, #246 | Referenced as historical context; no new findings | N/A |

### Step 3 — PR merge verification

`gh pr view 251 --json mergedAt,state` → `{"mergedAt":"2026-04-20T13:48:17Z","state":"MERGED"}`. Non-null confirmed pre-DONE.

### Step 4 — unresolved concerns (reminders)

See `Open reminders for operator / next session` below — also surfaced in the session's closing user message.

---

## Open reminders for operator / next session

1. **#234** — `provisionGeneric` CLI subcommand is an absolute prerequisite before Run 03 can start. A separate session + branch + PR must land first.
2. **#250** — pre-existing logo file-placement gap. Low-priority until Matrix Run 03/06 exercises `provision_mode="generic"`; at that point, decide (a) fix file-placement, (b) collapse `company_logo_location` to /tmp, (c) SCP direct to secrets dir, or (d) delete the inert upload path.
3. **Budget headroom** — 3000 s budget on attempt 6 = 1.85× over empirical 27.7 min. If provision slows (stage 7 restore is the usual culprit), this is tight. Consider re-widening to 3300–3600 s if the next 2–3 runs drift upward.
4. **Post-destroy tree drift** — after `destroy dev01`, two files show harmless drift: `config/wireguard/keys.sops.yml` (ciphertext rotation with identical plaintext) and `hosts_map.yml` (trailing blank line). `git checkout --` on both is the canonical clean-up. Worth a pipeline fix: destroy should leave the tree byte-identical to its pre-provision state.
5. **Self-check (Step 0)** pattern is new in accept-02. It caught nothing on attempt 6 (correct — all preconditions were clean), but the pattern deserves a port to accept-03/04/05/06/07 as each run's spec is authored. Consider a shared helper in `prototypes/cytoscape/tests/helpers.js`.
6. **accept-01 spec** now carries the same `execSync` try/catch hardening. Run 01's canonical green remains formally waived per MEMORY, but if it's ever re-attempted, the spec will handle the sync_check non-zero exit gracefully.
7. **#246** — the 5 acceptance-matrix agenda filenames still carry the pre-scrub token. No effect on pipeline; hygiene-only follow-up.

---

## Acceptance-of-minutes checklist

- [x] Objective stated.
- [x] Five D-decisions recorded with reasoning.
- [x] Every GH issue referenced confirmed current.
- [x] PR #251 `mergedAt` non-null (2026-04-20T13:48:17Z) — `feedback_pr_merge_before_session_close.md` satisfied.
- [x] Two new issues filed (#249 closed same session, #250 open); MEMORY.md tracker updated.
- [x] Side findings filed or explicitly dismissed with reason.
- [x] Working tree clean on `main`.
- [x] Session-close audit (Steps 1–4) executed; all forward-tense commitments have a durable home; all new issue findings posted to GH; PR `mergedAt` verified.
