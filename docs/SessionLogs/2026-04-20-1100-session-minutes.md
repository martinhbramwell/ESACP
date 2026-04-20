# Session Minutes — 2026-04-20 11:00 EDT — #234 provisionGeneric CLI (last Run-03 blocker)

**Branch:** `feat/234-cli-provision-generic` → merged to `main` as `86a7c1d`
**PR:** [#255](https://github.com/martinhbramwell/ESACP/pull/255) (MERGED 2026-04-20T15:00:42Z)

---

## Objective (entering)

Close the last pre-Run-03 blocker: implement `provisionGeneric` CLI subcommand — thin dispatcher composing the existing `macro.provision_generic.run` (stages 1-9) + `orchestration.wizard_run.run_wizard`. Mirrors the `addHost` pattern from PR #237.

## Status

**DONE.** PR #255 merged; #234 auto-closed via `fixes #234` trailer. Matrix Run 03 is now unblocked.

---

## Decisions recorded

| D | Question | Answer |
|---|---|---|
| D1 | Acceptance-test depth — e2e through the macro, or fast-reject paths only? | **Fast-reject paths only.** The macro runs stages 1-9 (hours, real VM). Test validates dispatcher correctness (argparse wiring + exit codes); macro e2e is Matrix Run 03's job. Same compromise used for `verify_add_host.py` (no real VM there either — it snapshot-restores `hosts_map.yml`). |
| D2 | CLI signature — copy API body exactly, or simplify? | Mirror API: `--wizard-mode {record\|replay\|existing}` + `--wizard-arg <name>`. Issue acceptance criterion: "Wizard mode selection mirrors API body shape." |
| D3 | Shared-primitive extraction between `job_worker.run_provision_generic` and this CLI? | **Deferred.** Both compose `macro.run + run_wizard` in 3 lines — same pattern as existing `cli/provision.py` vs `job_worker.run_provision`. Flagged in PR #255 body as a potential #235-class asymmetry if the composition grows; not blocking. |
| D4 | How to absorb `esacp.py` growth (106 → 109 after wiring) through the anti-spiral ratchet? | **Compact-to-absorb** (PR #237 pattern): folded `sub.required = True` into `sub = parser.add_subparsers(..., required=True)`, moved `provision_generic.add_subparser(sub)` adjacent to `add_host.add_subparser(sub)`. Net 106 → 106. Ratchet satisfied without bumping baseline. |
| D5 | PR merge strategy | Local `git merge --no-ff -S` → GPG-signed merge commit `86a7c1d`. Same D4 pattern as 09:48, 10:12, 10:43 sessions today. |

---

## Commits on this branch

| SHA | Title | Closes |
|---|---|---|
| `6885607` | feat(cli): provisionGeneric subcommand — fixes #234 | #234 |
| `86a7c1d` | Merge pull request #255 (signed merge commit on main) | auto-closed #234 |

## Changes shipped

- **`tools/cli/provision_generic.py`** (NEW, 75 lines) — thin dispatcher. Validates `wizard_mode` + `wizard_arg`, looks up `virbr0_ip` from `hosts_map.yml`, rejects hub nodes, derives `site_url` from `ZONE_DOMAINS[zone]`, calls `macro.provision_generic.run` then `orchestration.wizard_run.run_wizard`.
- **`tools/cli/verify_provision_generic.py`** (NEW, 69 lines, executable) — acceptance test covering 5 fast-reject paths (unknown VM, hub, replay w/o arg, existing w/o arg, invalid wizard-mode). Dynamic VM lookup via `hub_vm()` + first-non-hub iteration — no hardcoded VM names.
- **`tools/esacp.py`** (MOD, 106 → 106) — added `provision_generic` to import / `DISPATCH` / `VM_COMMANDS` / `add_subparser` call; absorbed +2 wiring lines by folding `required=True` into `add_subparsers()`.
- **`tools/CLAUDE.md`** — subcommand count 12 → 13.
- **`tools/size_baselines.json`** — auto-recorded the two new files (75, 69). Hook auto-stages.

## Acceptance (from #234)

- `./tools/esacp.py provisionGeneric <vm> --wizard-mode <record|replay|existing> [--wizard-arg <path>]` wired ✅
- `tools/cli/provision_generic.py` ≤ 80 lines (75) ✅
- Thin dispatcher — no business logic; composes existing macro + wizard primitive unchanged ✅
- Wizard mode selection mirrors API body shape (`NewGenericErpnextVM`) ✅
- Errors stream through `emit` (`console.print`); exit codes reflect stage failure (0/1/2) ✅
- Verify/acceptance test colocated (`tools/cli/verify_provision_generic.py`, 5/5 green) ✅
- Out of scope: no macro/wizard/recording/UI modifications — honored ✅

---

## Execution timeline

1. **Session start** — MEMORY.md + last-session minutes (2026-04-20-1043) loaded; `sync_check.sh` → 43 ✅ / 8 ⚠️ / 3 ❌ (3 failures = expected idle-VM pings, same baseline as last three sessions). Working tree clean on main.
2. **Objective framed** — Session 3 of the 3-session pre-Run-03 queue: "#234 — last Run-03 blocker." Approved.
3. **Discovery** — read `cli/add_host.py`, `cli/verify_add_host.py`, `cli/provision.py` (reference patterns); `api/routes/provision.py:42-60` (API endpoint shape + validation); `pipeline/macro/provision_generic.py` (no wizard in macro); `pipeline/orchestration/wizard_run.py` (record/replay/existing); `job_worker.py:run_provision_generic` (composition pattern); `api_models.py:NewGenericErpnextVM` (body shape); `cli/_common.py` (hub_vm, kvm_hosts, PROJECT_ROOT).
4. **Design presented** — file plan, exit codes, test scope (fast-reject only), explicit out-of-scope list. User approved.
5. **Branch** — `git checkout -b feat/234-cli-provision-generic` off main.
6. **Implementation** — Write `provision_generic.py` (75 lines), `verify_provision_generic.py` (69 lines, `chmod +x`), edit `esacp.py` (4 edits: import, DISPATCH, VM_COMMANDS, `add_subparser` call), edit `tools/CLAUDE.md` subcommand count.
7. **Verify (pre-commit)** — `./tools/cli/verify_provision_generic.py` → 5/5 green; `./tools/esacp.py provisionGeneric --help` → correct; `./tools/esacp.py --help` → `provisionGeneric` appears; `sync_check.sh` → no new failures (baseline idle-VM 3 ❌ unchanged).
8. **First commit attempt — size ratchet blocked** — `tools/esacp.py` grew 106 → 109. Mitigation: compact-to-absorb via `required=True` fold + repositioning `provision_generic.add_subparser(sub)`. `wc -l` → 106. Re-ran verify → 5/5 still green.
9. **Commit** — `6885607`, GPG-signed (`A232D66FDA9704E8`, good signature), Conventional-Commits `feat(cli)`, `fixes #234` trailer.
10. **Push** — `origin/feat/234-cli-provision-generic`.
11. **PR** — #255 opened against `main`. Paused for user approval before merge.
12. **User: "finish it off"** → local `git merge --no-ff -S` (merge commit `86a7c1d`, signed) → `git push origin main`.
13. **Verify** — `gh pr view 255 --json mergedAt` = `2026-04-20T15:00:42Z` (non-null, `feedback_pr_merge_before_session_close.md` satisfied); `gh issue view 234` → state=CLOSED, closedAt=`2026-04-20T15:00:41Z`.

---

## Issues closed this session

| # | Title | Closed via |
|---|---|---|
| **#234** | feat(cli): provisionGeneric subcommand (skeletal ERPNext + wizard) | `6885607` → PR #255 merge `86a7c1d` |

## Findings NOT filed (with reason)

- **`job_worker.run_provision_generic` vs `cli/provision_generic.run` — duplicated macro+wizard composition (3 lines each)** — identical pattern already exists in `cli/provision.py` vs `job_worker.run_provision`. User's durable guidance from today's 10:43 session (`feedback_not_perfection_project.md`) applies: 3-line duplication doesn't justify an extraction primitive yet. If the composition grows, file under #235. No new GH issue.
- **Pre-commit ratchet auto-persists baselines for new files even when the commit is blocked** — this is already tracked as **#238** ("bug(pre_commit_size_check): baselines persisted on blocked commits"). Observed again this session (the hook recorded `provision_generic.py`=75 and `verify_provision_generic.py`=69 before rejecting on `esacp.py` growth). No new issue needed.

---

## State at session close

- `main` at `86a7c1d` (signed merge commit). Branch `feat/234-cli-provision-generic` retained per `feedback_keep_merged_branches.md`.
- No VMs affected this session (pure CLI dispatcher + test).
- **Pre-Run-03 queue: 3 of 3 DONE** (#246, #253, #234). Matrix Run 03 has no known blockers.
- Working tree clean on `main`.

## What Matrix Run 03 needs next

1. **Agenda**: `docs/SessionLogs/acceptance-matrix/03-cli-vm-pseudo-company-wizard-creates-backup.md` (already scrub-renamed in PR #252).
2. **Run 03 exercises `provision_mode="generic"`**, which #250 (pre-existing, low-priority) notes will still show `company logo [SKIP]` because the upload path is inert. Run 03 is likely when the fix-or-explicitly-defer decision becomes actionable.
3. **Run 03 is the first time** `cli/provision_generic.py` + the Playwright wizard will run together end-to-end outside the API path. Budget accordingly (macro = hours).

---

## Open reminders for operator / next session

1. **Matrix Run 03** — first full e2e of the new CLI dispatcher. Agenda + plan already staged; no remaining blocker.
2. **#235 tracker (CLI/API asymmetry)** — 13 items tracked. Decompose opportunistically as each transport asymmetry surfaces in future Matrix runs; not a standalone project.
3. **#238** (ratchet auto-persists on blocked commits) — not a blocker for Matrix Run 03 but was observed again today. Low priority; fix when convenient.

---

## Session-close audit

### Step 1 — forward-tense resolution

| Phrase | Resolution |
|---|---|
| "I'll read the reference files before writing code" | `cli/add_host.py`, `cli/verify_add_host.py`, `cli/provision.py`, `api/routes/provision.py`, `macro/provision_generic.py`, `orchestration/wizard_run.py`, `api_models.py`, `job_worker.py`, `cli/_common.py` all read. |
| "OK to proceed" / full design plan (files, exit codes, tests) | All executed: branch, 4 edits + 2 new files, verify script green, commit `6885607`, PR #255, merge `86a7c1d`. |
| "Pausing before local --no-ff -S merge … Do you want me to finish it off?" | Resolved by user "Yes. Proceed." → merge executed. |
| "Flag `job_worker` vs CLI composition as potential future #235-class asymmetry if it grows" | Durable home: PR #255 body "Scope — explicitly NOT in this PR" + this minutes "Findings NOT filed". No task — conditional on future growth. |

### Step 2 — GH issues, comment audit

| Issue | New findings this session | Posted to GH? |
|---|---|---|
| **#234** | Design plan + acceptance-test scope rationale | PR #255 body + commit `6885607` message; auto-closed via `fixes #234`. |
| **#255** (PR) | Summary + test plan + compact-to-absorb rationale + explicit scope-exclusion | PR body at create time. |
| #235, #238, #250 | No new findings — historical context only | N/A |

### Step 3 — PR merge verification

`gh pr view 255 --json mergedAt,state,mergeCommit` → `{"mergedAt":"2026-04-20T15:00:42Z","state":"MERGED","mergeCommit":{"oid":"86a7c1d..."}}`. Non-null confirmed pre-DONE.

### Step 4 — unresolved concerns (reminders)

See "Open reminders for operator / next session" above.

---

## Acceptance-of-minutes checklist

- [x] Objective stated.
- [x] Five D-decisions recorded with reasoning.
- [x] Every GH issue referenced confirmed current.
- [x] PR #255 `mergedAt` non-null (2026-04-20T15:00:42Z) — `feedback_pr_merge_before_session_close.md` satisfied.
- [x] One issue closed (#234) — same session.
- [x] Side findings explicitly dismissed with reason + durable home cited.
- [x] Working tree clean on `main`.
- [x] Session-close audit (Steps 1–4) executed; all forward-tense commitments have a durable home; no new GH-issue findings pending posting; PR `mergedAt` verified.
- [x] Matrix Run 03 unblocked — pre-Run-03 queue closed (3/3).
