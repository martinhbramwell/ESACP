# 2026-04-27 1730 — Post-V14 housekeeping bundle

## Objective stated at session start
> Clear the post-V14-success residue list (13 items from the 1030 minutes' triage) by triaging settled-vs-open, executing the operator-approved housekeeping bundle (capture/delete snapshots on toshy, retention-principle decision, lesson capture, RAM-policy issue filing, minutes commit), and surfacing any blockers without fix-by-shortcut.

## Outcome
**Achieved.** Bundle landed direct-to-main per housekeeping exception (single-file docs commit, no substantive code). All 7 planned actions executed; the one operational blocker (saconsole_old qcow2 deletion) surfaced with the right honesty and was resolved by the operator at session close.

## What happened — by action

| # | Action | Result | Evidence |
|---|---|---|---|
| A | Capture `V14-baseline-2026-04-27` snapshot on dev02 (current-state safety) | ✅ created | `virsh -c qemu:///system snapshot-create-as dev02 V14-baseline-2026-04-27` |
| B | Delete `Pre-V14-attempt-2026-04-27` snapshot | ✅ deleted | `virsh snapshot-delete dev02 Pre-V14-attempt-2026-04-27` |
| C | Delete `Pre-V14-attempt-v2-6GB` snapshot | ✅ deleted | `virsh snapshot-delete dev02 Pre-V14-attempt-v2-6GB` |
| D | Write `feedback_domain_research_first_for_cross_major.md` + MEMORY.md pointer | ✅ written | `memory/feedback_domain_research_first_for_cross_major.md` |
| E | Commit 1030 minutes (housekeeping commit on main) | ✅ landed | `d1b3a47 docs: 2026-04-27 1030 session minutes — V13→V14 first ladder rung COMPLETE on dev02` (GPG-signed) |
| F | File GH issue for default dev VM RAM 4 → 6 GiB | ✅ filed | [#308](https://github.com/martinhbramwell/ESACP/issues/308) — design question (unconditional bump vs role-conditional) deferred to that session |
| G | Close #288 with retention-principle decision | ✅ closed | won't-fix close comment + follow-up comment 4330838265 |
| H | Delete `saconsole_old-2026-04-22-1951.{qcow2,seed.iso}` + preserved domain XML on toshy | ✅ deleted by operator | Stale `~/.ssh/.supwd.sh` rejected `sudo -A` 3× from this session; operator ran the deletion via TTY |

## Triage that preceded the bundle

The 1030 minutes had ended with a 13-item residue list. Operator triage at session start collapsed it to 5 real decisions + 1 housekeeping bundle:

| Original item | Verdict |
|---|---|
| 1+2 hrms+payments install + orphan tables | **Defer to #306 implementation session** |
| 3 V14-baseline snapshot | **Capture** (current-state safety only — not archive) |
| 3 Snapshot retention principle | **No backup snapshots — pipeline reproducibility is source of truth** (#288 closed on this) |
| 4 dev01 down per 1-VM rule | Steady state — drop from list |
| 5 #306 + #307 | Already filed — drop |
| 6 #302 verify-stage provision_mode | Already filed — drop |
| 7+13 V14 branch fate | **Keep as marker** — no action |
| 8 Ladder agenda framing lesson | Already in `feedback_check_tool_actual_cli_before_following_agenda.md` — drop |
| 9 Domain-research-first lesson | **Memory write** → `feedback_domain_research_first_for_cross_major.md` |
| 10 #300 PR #305 e2e gap | Already documented — drop |
| 11 BaRe #8 long-running tracker | Already filed — drop |
| 12 dev02 6 GiB RAM steady-state | **File issue for code change** → #308 |

## Retention principle established (this session, durable)

> "I see no reason to back up devxx VM snapshots since the whole point of this project is to be able to recreate them at any time."

Codified in #288's close comment and in MEMORY.md's V14 line:
- *Backup-only / archival* snapshots and preserved disk artefacts → **not retained**.
- *Current-state safety* snapshots during active work (e.g. V14-baseline-2026-04-27) → session-level conveniences, not long-term archive.
- Pipeline first, snapshot second, archive never.

## The one honest blocker

`SUDO_ASKPASS=~/.ssh/.supwd.sh sudo -A rm …` on toshy returned "3 incorrect password attempts." Per global conduct rule "no masking of errors / do not use destructive shortcuts," I did not retry with alternate auth. Surfaced to operator with two paths (interactive TTY via `! ssh -t` or askpass refresh); operator ran the deletion themselves. **Stale askpass on toshy is operator-environment debt** (per `feedback_gpg_agent_cache_ttl.md` policy: re-mention only when it next costs session time — not filing).

## Reads for the next session

- These minutes
- `memory/feedback_domain_research_first_for_cross_major.md` (new)
- #308 (queued — own 1:1:1 session for RAM 4 → 6 GiB code change)
- `~/.claude/plans/stockroom-ladder.md` for the broader ladder context
- Open issues: 25 (closed #288, opened #308 — net 0)

## State at session close

- **main tip**: `d1b3a47` (clean tree, no PRs ahead)
- **dev02**: V14 (Frappe 14.101.1 / ERPNext 14.92.14), 6 GiB RAM, V14-baseline snapshot captured
- **dev01**: still shut down per strict 1-VM rule
- **toshy**: ~33 GiB recovered from saconsole_old cleanup
- **Open issues**: 25 — #48, #65, #138, #153, #156, #157, #187, #202, #219, #223, #235, #240, #241, #278, #280, #284, #285, #290, #292, #296, #297, #302, #306, #307, #308

## Branch / commit policy

Single docs commit direct-to-main per housekeeping exception (no substantive code touched in the repo). Memory-file writes happen outside the repo and need no commit. No PRs opened, none needed.

## Reminder back to operator

- Stale `~/.ssh/.supwd.sh` on toshy bit `sudo -A` once this session. Will bite again the next time a pipeline path runs `sudo -A` on toshy from a non-TTY context. Refresh whenever convenient — not a session-blocker today.
