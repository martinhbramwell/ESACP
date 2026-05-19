# Session Minutes — Open-Issues Purge Plan Re-draft (Ladder Frame)

**Date:** 2026-04-23 ~06:20–07:15 EDT
**Branch:** `main` (no feature branch; planning-only session)
**Commits:** none yet — minutes + memory edits only, committed after this file lands
**PRs:** none
**Issues closed:** none
**Issues opened:** none
**Issue comments posted:** #202, #187
**Baseline:** entered at `main @ a335631` (2026-04-22 1951 minutes tip)

## Declared objective

Re-evaluate and re-draft `~/.claude/plans/open-issues-purge.md` against
the short-term priority (ERPNext version-upgrade ladder), replacing the
2026-04-21 matrix-blast-radius draft which went stale when the matrix
closed 7/7 and the ladder was declared. Planning-only — no code, no
issue mutations beyond the findings-posting rule.

## What happened

### Re-evaluation

Mapped all 18 open issues against the stated ladder gate
(`project_upgrade_v13_to_v16.md`). Two cross-cutting rules narrowed
the field: `feedback_mission_priority_check.md` (ask what mission pillar
the pain affects) and `feedback_not_perfection_project.md` (size fixes
to pain). Most of the 18 landed in "strategic / research / tech debt
with no ladder-forcing function" — candidates for a parking lot, not
more sequencing.

Operator pushback corrected the shorthand "V13 → V16" mid-draft: the
ladder is **three sequential migrations** (v13→v14→v15→v16), each
gated by the Playwright regression suite. Dev-VM churn therefore
scales by 3×, which promoted `#202` (cloud-init templating from
`hosts_map.yml`) from default-park into the ladder-support tier.

### Re-draft structure

New plan at `~/.claude/plans/open-issues-purge.md` (258 lines, Appendix
A preserves the prior plan verbatim):

| Tier | Sessions | Issues | Intent |
|---|---|---|---|
| 0 — Quick wins | 1 | #278, #288 | housekeeping bundle (nagging sync_check + retention disposition) |
| 1 — Ladder support | 2 | #285 (+ #284 by-product), **#202** | wizard-backup parity cold regen + cloud-init template (promoted 2026-04-23) |
| 2 — Judgment calls | 0–3 | #280, #187, #219 | default-park with scope-pass on lift |
| 3 — Park | 0 | #48, #65, #138, #153, #156, #157, #223, #235, #240, #241 (+ #219 if not lifted) | parking-lot comments with explicit revisit triggers |

Exit condition replaces the old "zero open issues" gate: the
**first rung (v13→v14)** is unblocked when Tier 0 + Tier 1 close,
every Tier 3 issue carries a revisit-trigger comment, and Tier 2
has been scope-passed (each either actively scheduled or parked with
a trigger).

Cost projection: **3 sessions, ~2 matrix re-runs, ~30–40 min wall
time** — vs. the prior 12-session / 26-run / ~10-hour projection.
Collapse comes from honest parking, not shortcutting.

### Ladder-terminology correction (mid-session)

Operator question "Do you really intend to jump from v13 to v16,
skipping v14 & v15?" caught a sloppy shorthand that had crept into
the first pass of the plan file. Second pass corrected:

- Title → "v13→v14→v15→v16 Ladder"
- Body → "ladder", "rung", "each rung gated by Playwright regression
  suite" throughout
- Target frame → first rung (v13→v14), not all of V16
- `#202` promoted from Tier 2 (default park) to Tier 1
  (ladder-support) on ladder-churn argument
- `#187` gained a conditional dependency on `#202`'s outcome
  (lift-from-park trigger)
- Exit condition → unblocks v13→v14 specifically; subsequent rungs
  get their own planning sessions when predecessor certifies green
- Matrix cost ledger → 2→3 sessions, 1→~2 re-runs
- `MEMORY.md` → "Short-Term Priority — ERPNext v13 → v14 → v15 → v16
  ladder" with the rung-by-rung phrasing

### Findings posted to issues (audit step 2)

Two issues received state-changing findings that belong on the issue
per `GitHub Issues as institutional memory`:

- **#202** — promotion from default-park to Tier 1 with rationale:
  <https://github.com/martinhbramwell/ESACP/issues/202#issuecomment-4303600579>
- **#187** — park classification with revisit-trigger tied to #202
  outcome:
  <https://github.com/martinhbramwell/ESACP/issues/187#issuecomment-4303600891>

Other 16 issues received only tier/trigger classifications, which is
the scheduled Tier 0 parking-lot sweep — not a finding, per the plan.

## Audit (session-close)

1. **Forward-tense phrases** — all resolved against tool-call
   evidence or plan-file durable homes (Write call for the plan,
   Edit calls for the revisions, Edit call for `MEMORY.md`).
   Parking-lot comment sweep explicitly scoped to Tier 0 session,
   not leaked to minutes-as-home.
2. **GH issue findings** — #202 and #187 comments posted before
   writing minutes. Other 16 issues' tier assignments are the Tier
   0 parking-lot sweep, explicitly scoped.
3. **PRs** — none opened.

## Files changed

| File | Change |
|---|---|
| `~/.claude/plans/open-issues-purge.md` | full re-draft (258 lines); Appendix A preserves prior 2026-04-21 plan verbatim |
| `memory/MEMORY.md` | "Short-Term Priority" header + body reframed rung-by-rung; notes 2026-04-23 revision and #202 promotion |
| `internal_docs/SessionLogs/2026-04-23-0620-session-minutes.md` | this file |

Issue comments (not file changes, but durable homes):
- #202 → issuecomment-4303600579
- #187 → issuecomment-4303600891

## State handed to next session

- `main @ <this minutes commit>` (after minutes commit+push).
- **Open issues: 18** — unchanged. No mutations this session.
- Plan file now current; first-move declared as Tier 0 bundle
  (#278, #288).
- Next session should piggyback the parking-lot comment sweep
  (11 Tier 3 comments + any Tier 2 scope-pass outcomes) onto the
  Tier 0 housekeeping session per `open-issues-purge.md` → "Session
  discipline reminders".

## Reminders to user (unresolved concerns)

1. **`project_upgrade_v13_to_v16.md` is still a stub.** Once Tier 0
   + Tier 1 close, a dedicated planning session for the v13→v14
   rung specifically (not the whole ladder) is the natural next gate.
2. **Parking-lot comment sweep is deferred.** 11 Tier 3 issues plus
   scope-pass outcomes for Tier 2 (#280, #219) must have comments
   posted by end of the Tier 0 session, else the plan's exit
   condition is not met.
3. **#288 retention decision is undecided.** Disposition call
   (retain / delete-after-N-days / archive-XML-only) is Tier 0
   scope; 33 GiB on toshy with no disposition.
4. **`#187` ↔ `#202` dependency is now live.** If `#202`'s
   cloud-init template rollout exposes deeper `buildVM` damage,
   `#187` lifts out of park for its own session. Otherwise stays
   parked.
5. **`#227` (WG spoke re-enrollment) remains open but dormant**,
   carried over from 2026-04-22 1951 minutes. Not in the purge
   plan because it's not an ESACP open issue count drag (Play 5 of
   the Ansible provision re-enrolls the controller spoke
   automatically; only non-controller spokes remain in scope and
   none currently exist on the mesh).

## File trail

- Re-drafted plan: `~/.claude/plans/open-issues-purge.md`
- Memory update: `memory/MEMORY.md` (short-term priority section)
- #202 promotion comment:
  <https://github.com/martinhbramwell/ESACP/issues/202#issuecomment-4303600579>
- #187 park-with-trigger comment:
  <https://github.com/martinhbramwell/ESACP/issues/187#issuecomment-4303600891>
- This minutes: `internal_docs/SessionLogs/2026-04-23-0620-session-minutes.md`
- Prior minutes: `internal_docs/SessionLogs/2026-04-22-1951-session-minutes.md`
  (#220 Run 01 acceptance)
