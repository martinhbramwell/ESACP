# 2026-06-08 2145 — Session 115 minutes

> Objective (pinned): **(A) Pivot to V13→V15 migration-with-data testing under #480.** Resolved
> into a **planning session** (like S108) — objective A presupposed a data-level run S108 had
> explicitly deferred, and the substantive work needs its own 1:1:1 branch. Deliverables:
> approved plan (`~/.claude/plans/v13-v15-migration-with-data.md`), tracking issue **#671**,
> a memory note, session logs. **No ESACP code touched; clean tree.**

## Class

Planning session under the #480 umbrella. No substantive ESACP code change. **Not** an
introspection-sidebar (no MEMORY.md *restructuring* — only a single feedback-pointer append;
no carry-forward attrition of the mechanical kind). One issue filed (#671).

## What happened

### Course-correction (the important part)
Mid-scoping I wrongly told the operator the V13→V15 path was "starting from scratch," off a
**`main`-only grep** that saw `upgrade_v14/` (V13→V14) + R1/R3 fixups and nothing else. The
operator pushed back (they had watched a working V13→V16 exploratory migration). Reconciliation
proved them right:
- The **V13→V16 exploratory migration ran** on dev02 (from S79) and worked.
- **S108 already did the V13→V15 re-validation** (`feat/480-v15-catalog-delta`, merged #646),
  re-reading the catalog against live frappe/erpnext 15.110.0 source and retitling #480 to
  "V13→V15 baseline + V15→V16 tracked."
- The #626 + R8/#617 fixups are committed on **`umbrella/v16-clean-run`** (`af5b3ab`,
  `df6246f`) — invisible to a main-only search.
- I also overstated the sequential-major constraint.
Lesson captured as memory `feedback_check_branches_and_minutes_before_declaring_absent` +
MEMORY.md index line.

### The S108 delta confirms V13→V15 is the *easier* leg
Two of the nastiest V16 defects don't apply to V13→V15: **R1** (Homepage doctype **alive** on
V15) and **#618** (V15 sidebar **surfaces** private workspaces) — both flip to the V15→V16 leg,
as does leaderboard. The **V13→V15 leg** carries only #626 (Server Scripts/commission logic),
#617/R8 (naming series), R3 (IRS-1099), R5/R6 (nginx, provision-time).

### Plan authored (approved-in-principle)
`~/.claude/plans/v13-v15-migration-with-data.md`. Two operator decisions taken:
1. **Mechanism A** (restore real V13 prod backup from `$BESPOKE_ROOT/ce_sri/BKP/` onto the clean
   V15 `dev15_01` → single `bench migrate` replays V14+V15 patches → V15-leg fixups → verify).
   Chosen over Mechanism B (in-place `bench switch-to-branch` chain on dev01): fits the existing
   substrate, one-VM-at-a-time (no dev01 boot), mirrors the real Beaverdam cutover, reuses
   `applySubstrateMigration` (#418).
2. **Branch off `umbrella/v16-clean-run`** (it carries #626 + R8, not on main).
Acceptance: migrate exit 0 + full log; #617/#626/R3 probes pass on real data; LogiSoluValidations
suite confirms bespoke functionality; data-level delta posted on #480. Watchpoints: single-jump
migrate may mask per-major breakage (a failure is a *finding*); `data_restore.sh` may need an
adapter to run onto an already-built V15 bench.

## Counts / state
- ESACP open: **85 → 86** (+1 filed: **#671**; 0 closed). LSKB: **13**.
- sync_check at start: 46✅/11⚠/4❌ — the 4 ❌ are dev01/dev02 shut-off (by design); §18 suite
  **62/62** green. TRIVIAL_FIXES: 1 monitor-only (S33), no action.
- main tip unchanged by code (this close commits session logs only). VMs: saconsole + dev15_01
  running; dev01/dev02 shut off by design. Junior's `onBoardingQRcode.png` untracked (as at start).
- **Clock skew noted:** system clock read `2024` while the S115 agenda was stamped `2135` (same
  day). `agenda_lint.latest_agenda()` sorts by **filename**, so this pair is stamped `2145` to
  preserve ordering. Operator may wish to check controller time.

## Diff-based introspection-sidebar trigger: NEGATIVE
No MEMORY.md index *restructuring* (single append, not add/remove/reorder of the indexing
scheme); no carry-forward attrition. Housekeeping-style doc close, not a sidebar.

## #653 deferred-acceptance check (from S115 pre-flight)
Not exercised this session — no `tools/pipeline/**` edit occurred to contrast against the
allowlisted SessionLogs/memory edits. The SessionLogs + memory edits this close are the
allowlist's intended no-prompt path; carry the explicit contrast check to a session that touches
both surfaces.
