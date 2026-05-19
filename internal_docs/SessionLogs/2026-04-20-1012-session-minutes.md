# Session Minutes — 2026-04-20 10:12 EDT — #246 acceptance-matrix agenda scrub

**Branch:** `chore/246-acceptance-matrix-scrub` → merged to `main` as `ad997f9`
**PR:** [#252](https://github.com/martinhbramwell/ESACP/pull/252) (MERGED 2026-04-20T14:15:14Z)

---

## Objective (entering)

Resolve **#246** — rename + body-scrub the 5 acceptance-matrix agenda files under `docs/SessionLogs/acceptance-matrix/` — as the smallest, fastest item on the pre-Run-03 queue. First of three sessions the user triaged from the 2026-04-20 09:48 close-out reminders.

## Status

**DONE.** PR #252 merged; #246 auto-closed via `fixes #246` trailer.

---

## Decisions recorded

| D | Question | Answer |
|---|---|---|
| D1 | Triage of the 7 post-Run-02 reminders — resolve all before Run 03? | No. Split into 3 sessions: (1) #246 this session, (2) new "byte-identical destroy" issue + fix, (3) #234 folding reminders 3+5. Reminders 2 and 6 non-actionable (see D2) |
| D2 | Reminders 2 (#250) and 6 (accept-01 hardening) — mark "resolved/non-actionable" in MEMORY? | No. #250 is already tracked as an open GH issue; accept-01 hardening is already recorded in the 2026-04-20 09:48 minutes (commit `750d97f`). MEMORY scope confirmation only, no edits |
| D3 | Session-log carve-out — scrub `docs/SessionLogs/*-minutes.md` pointers to the 2 renamed files? | No. Per #239 PR #242, `docs/SessionLogs/**` is the historical carve-out. Only the 5 matrix-agenda files are "future-work"; session minutes are frozen |
| D4 | Live SUT pointer at `accept-02-cli-full-company-specific.spec.js:17` — update? | Yes. Strictly outside the #246 "plans/memory/agendas" acceptance text, but it is a live comment pointing at a renamed path. Updated in the same PR |
| D5 | Memory pointers — `feedback_no_real_client_names.md` illustrative placeholder + `feedback_compound_cmd_hook.md` hook-filename | Left as-is. The first is the rule's example token; the second is the on-disk filename tracked by #243 |

---

## Commits on this branch

| SHA | Title | Closes |
|---|---|---|
| `e464942` | chore(scrub): acceptance-matrix agenda rename + body scrub (#246) | #246 |
| `ad997f9` | Merge pull request #252 (signed merge commit on main) | auto-closed #246 |

## Changes shipped

- **Renamed** (via `git mv`, history preserved):
  - `02-cli-vm-full-logichem-from-backup.md` → `02-cli-vm-full-company-specific-from-backup.md`
  - `05-ui-vm-full-logichem-from-backup.md` → `05-ui-vm-full-company-specific-from-backup.md`
- **Body-scrubbed** (5 files): `02`, `03`, `05`, `06`, `07` — `company-specific` (kebab, prose), `full_company_specific` (snake, YAML data), per the #239 convention.
- **Live pointer**: `prototypes/cytoscape/tests/accept-02-cli-full-company-specific.spec.js:17` — agenda-filename comment updated from the frozen old filename to the new one; stripped the "(filename frozen pending #246; new artifacts use company-specific token)" parenthetical that no longer applies.

## Acceptance (from #246)

- `grep -ri 'logichem' docs/SessionLogs/acceptance-matrix/` → **zero hits** ✅
- No plan, memory, or other-agenda pointer left referencing the old filenames ✅
- Landed before Run 03 begins (Run 03 separately blocked by #234) ✅

---

## Execution timeline

1. **Session start** — standard protocol: MEMORY.md read, last-session minutes loaded (2026-04-20-0948), `sync_check.sh` → 43 ✅ / 8 ⚠️ / 3 ❌ (3 failures all expected idle-VM pings; same baseline as last session). Working tree clean on main.
2. **User triage** — presented the 7 post-Run-02 reminders from the 0948 close; pushed back on bundling them into one session (violates 1:1:1); proposed 3-session split. User approved "#1" (= #246).
3. **Pre-scrub inventory** — grepped `logichem` scope, enumerated pointers across plan/memory/session-logs/SUT. Classified 5 hits outside matrix-agenda dir as carve-out (session logs) or out-of-scope (#243-tracked hook file, illustrative placeholder).
4. **Scrub** — `Write` for the 2 heavily-edited files (02, 05, ~9 replacements each), `Edit` for 03/06/07 single-line replacements and the spec.js comment.
5. **Rename** — `git mv` on the 2 agenda files.
6. **Verify** — re-grep `logichem` on matrix-agenda dir → zero.
7. **Commit** — `e464942`, GPG-signed (RSA A232D66FDA9704E8, good signature), Conventional-Commits `chore(scrub)`, `fixes #246` trailer.
8. **Push** — `origin/chore/246-acceptance-matrix-scrub`.
9. **PR** — #252 opened against `main`.
10. **Merge** — user approval → local `git merge --no-ff -S chore/246-acceptance-matrix-scrub` on main (signed merge commit `ad997f9`, per D4 pattern from the 2026-04-20 09:48 minutes) → `git push origin main`.
11. **Verify** — `gh pr view 252 --json mergedAt` = `2026-04-20T14:15:14Z` (non-null, per `feedback_pr_merge_before_session_close.md`); `gh issue view 246` state=CLOSED, closedAt=2026-04-20T14:15:13Z.

---

## Issues filed this session

None.

## Issues closed this session

| # | Title | Closed via |
|---|---|---|
| **#246** | chore(scrub): rename + body-scrub the 5 acceptance-matrix agenda files (post-#239 follow-on) | `e464942` → PR #252 merge `ad997f9` |

---

## Findings NOT filed (with reason)

- **`docs/SessionLogs/*-minutes.md` historical references to the old agenda filenames** — per #239 PR #242 carve-out, session logs are frozen as written. Four files hit: `2026-04-20-0802-session-minutes.md`, `2026-04-19-1242-next-agenda.md`, `2026-04-19-0805-next-agenda.md`, `2026-04-18-0652-session-minutes.md`. Left as-is by design, captured explicitly in PR #252 body.

---

## State at session close

- `main` at `ad997f9` (signed merge commit). Branch `chore/246-acceptance-matrix-scrub` retained per `feedback_keep_merged_branches.md`.
- No VMs affected this session (doc-only + spec-comment change).
- Pre-Run-03 queue: **1 of 3 done** (#246 closed). Next: new "byte-identical destroy" issue + fix. Final: #234 provisionGeneric CLI.

---

## Open reminders for operator / next session

These are carried forward from the 2026-04-20 09:48 close; updated to reflect this session's progress.

1. **#234** — `provisionGeneric` CLI subcommand — **absolute prerequisite** before Run 03. Own branch + own session.
2. **New issue + fix — byte-identical destroy** — after `destroy dev01`, `config/wireguard/keys.sops.yml` shows ciphertext rotation with identical plaintext; `hosts_map.yml` gains a trailing blank line. Pipeline fix: destroy must leave the tree byte-identical. File the issue first; implement on its own branch.
3. **#250** — logo file-placement gap. Non-actionable until Matrix Run 03/06 exercises `provision_mode="generic"`. Remains open.
4. **Budget 3000s** — to fold into the #234 session as a one-line param decision (keep or widen to 3300–3600s if provision slows).
5. **Step-0 self-check → `helpers.js`** — accept-03 through accept-07 specs do not exist yet. Extract the helper during the #234 session (when accept-03's spec is authored) to avoid premature abstraction.
6. **accept-01 execSync hardening** — already done in `750d97f` (2026-04-20 09:48 session). No outstanding action. Recorded here for close-out completeness.
7. **MEMORY.md update** — this session's close updates the GitHub-institutional-memory paragraph to remove #246 from open-issues list + record the merge commit. (Performed as part of these minutes.)

---

## Session-close audit

### Step 1 — forward-tense resolution

| Phrase | Resolution |
|---|---|
| "I'll start with #246" | Executed: branch → scrub → rename → commit → PR → merge |
| "I'll pause here to confirm before network-facing actions" | Executed: paused, user confirmed, then pushed |
| "CLI/API parity gaps get appended to #235, not fixed" (scope rule) | Durable home: MEMORY.md `#235 (tracker, non-blocking)` entry already present |
| "Reminders 2 and 6 — mark resolved/non-actionable and close out in MEMORY when appropriate" | Resolution: D2 above — deliberate no-op. Captured in these minutes in lieu of MEMORY edits |
| "I'll do the local `git merge --no-ff -S` onto main ... mergedAt non-null before marking done" | Executed: `ad997f9` signed, main pushed, mergedAt=2026-04-20T14:15:14Z |
| "🔜 Byte-identical destroy (reminder 4) / 🔜 #234 provisionGeneric" | Durable home: these minutes' "Open reminders" section + MEMORY.md pre-Run-03-queue update |

### Step 2 — GH issues, comment audit

| Issue | New findings this session | Posted to GH? |
|---|---|---|
| **#246** | Scrub executed; grep clean; spec.js pointer updated; session-log carve-out honored | PR #252 body + commit `e464942` message; issue auto-closed via `fixes #246` trailer |
| #234 | No new findings — Run-03 blocker reference only | N/A |
| #235, #239, #243, #247, #250 | No new findings — historical context only | N/A |

### Step 3 — PR merge verification

`gh pr view 252 --json mergedAt,state,mergeCommit` → `{"mergeCommit":{"oid":"ad997f9..."},"mergedAt":"2026-04-20T14:15:14Z","state":"MERGED"}`. Non-null confirmed pre-DONE.

### Step 4 — unresolved concerns (reminders)

See "Open reminders for operator / next session" above — surfaced verbatim in the session's closing user-facing message.

---

## Acceptance-of-minutes checklist

- [x] Objective stated.
- [x] Five D-decisions recorded with reasoning.
- [x] Every GH issue referenced confirmed current.
- [x] PR #252 `mergedAt` non-null (2026-04-20T14:15:14Z) — `feedback_pr_merge_before_session_close.md` satisfied.
- [x] Zero new issues filed; one issue (#246) closed.
- [x] Side findings filed or explicitly dismissed with reason.
- [x] Working tree clean on `main`.
- [x] Session-close audit (Steps 1–4) executed; all forward-tense commitments have a durable home; no new GH-issue findings pending posting; PR `mergedAt` verified.
