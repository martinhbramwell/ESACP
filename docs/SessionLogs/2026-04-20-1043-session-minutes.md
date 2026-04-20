# Session Minutes — 2026-04-20 10:43 EDT — #253 hosts_map.yml byte-identical destroy

**Branch:** `fix/253-destroy-hosts-map-blank-line` → merged to `main` as `e0ce3c9`
**PR:** [#254](https://github.com/martinhbramwell/ESACP/pull/254) (MERGED 2026-04-20T14:42:05Z)

---

## Objective (entering)

Close out the "byte-identical destroy" item — Session 2 of 3 from the pre-Run-03 queue triaged on 2026-04-20 09:48. File an issue for the post-destroy tree drift on `hosts_map.yml` + `config/wireguard/keys.sops.yml`, then fix it on its own branch so `destroy <vm>` leaves the tree byte-identical when no logical state changed.

## Status

**DONE — narrower than entered.** PR #254 merged; #253 auto-closed via `fixes #253` trailer. Only Fix A (hosts_map.yml deterministic drift) landed. Fix B (keys.sops.yml ciphertext rotation) deliberately de-scoped per user guidance.

---

## Decisions recorded

| D | Question | Answer |
|---|---|---|
| D1 | Fix scope — A (hosts_map.yml) + B (keys.sops.yml), or A only? | **A only.** User: "purging every last microscopic issue is NOT a project goal." Sized the fix to the operator pain actually reported; the `git checkout -- config/wireguard/keys.sops.yml` manual workaround is acceptable. |
| D2 | Should a separate issue be filed for the ciphertext rotation? | No — not painful enough to warrant a tracked issue. Documented inline in #253 body's "Scope — explicitly NOT fixed here" section + PR #254 body. File a follow-on only if it becomes painful during Run 03+. |
| D3 | Replacement string in `hosts_map_remove.py` — `""` or `"\n"`? | `""`. `build_host_block()` emits a block starting with `\n`, so the remove-path pattern already consumes the leading `\n`; replacing with another `\n` re-inserts the glue newline. Verified byte-identical via simulation before editing. |
| D4 | Capture user's scope-framing as a durable memory? | Yes — `memory/feedback_not_perfection_project.md` created + indexed in `MEMORY.md` under "Critical Rules". |
| D5 | PR merge strategy | Local `git merge --no-ff -S` → guaranteed GPG-signed merge commit `e0ce3c9`. Same D4 pattern as 09:48 and 10:12 sessions. |

---

## Commits on this branch

| SHA | Title | Closes |
|---|---|---|
| `61a1191` | fix(destroy): remove_from_hosts_map leaves tree byte-identical | #253 |
| `e0ce3c9` | Merge pull request #254 (signed merge commit on main) | auto-closed #253 |

## Changes shipped

- **`tools/pipeline/orchestration/hosts_map_remove.py:20`** — one-char fix: `re.sub(pattern, "\n", text)` → `re.sub(pattern, "", text)`. The `\n{3,}` collapse below it stays as defense-in-depth.
- **`tools/pipeline/orchestration/test_hosts_map_remove.py`** — new colocated round-trip test (57 lines, executable with `#!/usr/bin/env python3` + `chmod +x`). Asserts `build_host_block` → insert-at-MARKER → `remove_from_hosts_map` produces byte-identical output to the starting `hosts_map.yml`. Fails on `main`; passes on this branch.
- **`tools/size_baselines.json`** — ratchet auto-updated by pre-commit hook.
- **Auto-memory**: `feedback_not_perfection_project.md` added; `MEMORY.md` pointer inserted under "Critical Rules".

## Acceptance (from #253)

- Colocated round-trip test passes: `./tools/pipeline/orchestration/test_hosts_map_remove.py` → `OK  add→remove round-trip is byte-identical` ✅
- Ad-hoc reproducer from #253 body passes on this branch, fails on `main` ✅
- Both files under the 80-line cap (26 + 57) ✅
- Keys-sops.yml rotation explicitly scoped out of this issue, with rationale documented ✅

---

## Execution timeline

1. **Session start** — standard protocol: MEMORY.md + last-session minutes (2026-04-20-1012) loaded, `sync_check.sh` → 43 ✅ / 8 ⚠️ / 3 ❌ (3 failures = expected idle-VM pings, same baseline as last two sessions). Working tree clean on main.
2. **Objective framed** — Session 2 of the 3-session pre-Run-03 queue: "byte-identical destroy". Proposed objective to user; approved.
3. **User pushback on scope** — before filing the issue, user asked "Why should I care about this issue at all?" Honest cost-benefit response: ~5s manual cleanup vs. pipeline complexity. User replied: suspended long-term goals, patient clean-up phase, Fix A only, explicit "purging every last microscopic issue is **NOT** a project goal."
4. **Feedback captured** — wrote `feedback_not_perfection_project.md` + MEMORY.md index entry BEFORE executing the fix (so the framing survives even if the fix had been interrupted).
5. **Investigation** — Read `macro/destroy.py`, `hosts_map_remove.py`, `sops_key_remove.py`, `host_registration.py`, `host_registration_block.py`. Identified the add/remove asymmetry (leading `\n` in `build_host_block` → glue `\n` in `remove_from_hosts_map`).
6. **Reproducer simulation** — Bash one-liner round-tripping `build_host_block` against the live `hosts_map.yml`: current code fails byte-identity with a `+` blank line; `""`-replacement fix passes.
7. **Issue filed** — #253 with full root-cause, reproducer, fix, explicit scope-exclusion of keys.sops.yml.
8. **Branch** — `git checkout -b fix/253-destroy-hosts-map-blank-line` off main.
9. **Fix** — single `Edit` on `hosts_map_remove.py:20`. Test written + `chmod +x` + run → green.
10. **Commit** — `61a1191`, GPG-signed (`A232D66FDA9704E8`, good signature), Conventional-Commits `fix(destroy)`, `fixes #253` trailer.
11. **Push** — `origin/fix/253-destroy-hosts-map-blank-line`.
12. **PR** — #254 opened against `main`. Paused for user approval before merge.
13. **User: "finish it off"** → local `git merge --no-ff -S` (merge commit `e0ce3c9`, signed) → `git push origin main`.
14. **Verify** — `gh pr view 254 --json mergedAt` = `2026-04-20T14:42:05Z` (non-null, `feedback_pr_merge_before_session_close.md` satisfied); `gh issue view 253` state=CLOSED, closedAt=2026-04-20T14:42:05Z.
15. **MEMORY.md** — "Open issues" line updated with #253 CLOSED entry.

---

## Issues filed this session

| # | Title | Role |
|---|---|---|
| **#253** | bug(destroy): hosts_map.yml gains a blank line after add→remove cycle | Filed + fixed + closed same session |

## Issues closed this session

| # | Title | Closed via |
|---|---|---|
| **#253** | bug(destroy): hosts_map.yml gains a blank line after add→remove cycle | `61a1191` → PR #254 merge `e0ce3c9` |

---

## Findings NOT filed (with reason)

- **`config/wireguard/keys.sops.yml` post-destroy ciphertext rotation** — inherent to `sops encrypt` (random DEK/nonce per write). No in-pipeline fix without git coupling and operator-safety gates. User explicitly de-scoped per "not a perfection project" (D1). Durable home: #253 body "Scope — explicitly NOT fixed here" + PR #254 body + `feedback_not_perfection_project.md`. Manual workaround `git checkout -- config/wireguard/keys.sops.yml` remains canonical.

---

## State at session close

- `main` at `e0ce3c9` (signed merge commit). Branch `fix/253-destroy-hosts-map-blank-line` retained per `feedback_keep_merged_branches.md`.
- No VMs affected this session (pure pipeline + test + doc change).
- Pre-Run-03 queue: **2 of 3 done** (#246 + #253 closed). Next: **#234** `provisionGeneric` CLI — sole remaining Run-03 blocker.
- Working tree clean on `main`.

## What unblocks Run 03

1. **#234** — `provisionGeneric` CLI subcommand. Absolute prerequisite. Own branch + own session (`feat/234-cli-provision-generic`).
2. Agenda file `docs/SessionLogs/acceptance-matrix/03-cli-vm-pseudo-company-wizard-creates-backup.md` is already scrub-renamed (PR #252 merged earlier today).

---

## Open reminders for operator / next session

1. **#234** — `provisionGeneric` CLI is the **last** pre-Run-03 blocker. One session, one branch, one PR. Reminders 3 + 5 from the 09:48 close (budget-3000s review + Step-0 self-check → `helpers.js`) fold into that session naturally.
2. **#250** — pre-existing logo file-placement gap. Non-actionable until Run 03/06 exercises `provision_mode="generic"`. Remains open.
3. **keys.sops.yml ciphertext rotation** — no GH issue filed. If this becomes painful during Run 03+ cycles, file a new issue citing #253's scope-exclusion paragraph as the prior deliberation. Workaround `git checkout -- config/wireguard/keys.sops.yml` stays canonical until then.
4. **`feedback_not_perfection_project.md`** — new durable rule. Apply when scoping fixes going forward: size to the pain, not to a theoretical "done" state; propose deterministic part + messy part separately and default to the deterministic one alone.

---

## Session-close audit

### Step 1 — forward-tense resolution

| Phrase | Resolution |
|---|---|
| "I'll investigate the destroy pipeline before filing" | Read + Grep + simulation Bash executed |
| "Saving that framing to memory first" | `memory/feedback_not_perfection_project.md` written + MEMORY.md indexed |
| "File GH issue" / "Branch off main" / "Edit `hosts_map_remove.py:20`" / "Add colocated test" / "GPG-signed commit" / "push, PR, local `--no-ff -S` merge" (full execution plan) | All executed: #253, `fix/253-destroy-hosts-map-blank-line`, `61a1191`, `test_hosts_map_remove.py`, GPG-verified, PR #254, merge `e0ce3c9` |
| "File a separate one if it ever becomes painful" (conditional, ciphertext rotation) | Durable homes: #253 body + PR #254 body + `feedback_not_perfection_project.md`. No open task (conditional on future pain). |
| "Pausing before the local `--no-ff -S` merge … Do you want me to proceed" | Resolved by user "finish it off" → merge executed |
| "Pre-Run-03 queue: 1 of 2 remaining items done … #234 remains the sole Run-03 blocker" | Durable home: MEMORY.md `#234 (blocker for Run 03)` entry + this minutes' "What unblocks Run 03" |

### Step 2 — GH issues, comment audit

| Issue | New findings this session | Posted to GH? |
|---|---|---|
| **#253** | Full root-cause + reproducer + fix + scope-exclusion of keys.sops.yml | Issue body (author-time) + PR #254 body + commit `61a1191` message; auto-closed via `fixes #253` trailer |
| **#254** (PR) | Summary + test plan + scope rationale | PR body at create time |
| #234, #246, #247, #248, #249, #250 | No new findings — historical context only | N/A |

### Step 3 — PR merge verification

`gh pr view 254 --json mergedAt,state,mergeCommit` → `{"mergedAt":"2026-04-20T14:42:05Z","state":"MERGED","mergeCommit":{"oid":"e0ce3c9..."}}`. Non-null confirmed pre-DONE.

### Step 4 — unresolved concerns (reminders)

See "Open reminders for operator / next session" above — also surfaced in the session's closing user-facing message.

---

## Acceptance-of-minutes checklist

- [x] Objective stated.
- [x] Five D-decisions recorded with reasoning.
- [x] Every GH issue referenced confirmed current.
- [x] PR #254 `mergedAt` non-null (2026-04-20T14:42:05Z) — `feedback_pr_merge_before_session_close.md` satisfied.
- [x] One issue filed (#253), one closed (#253) — same session.
- [x] Side findings (keys.sops.yml ciphertext rotation) explicitly dismissed with reason + durable home cited.
- [x] Working tree clean on `main`.
- [x] Session-close audit (Steps 1–4) executed; all forward-tense commitments have a durable home; no new GH-issue findings pending posting; PR `mergedAt` verified.
