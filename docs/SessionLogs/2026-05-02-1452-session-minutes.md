# 2026-05-02 1452 — Session minutes

**Branch:** `chore/check-tools-ruamel-326` → merged via PR #336 → `main` tip `a3aa241`.
**Objective:** Session 2 of 4 — close #326 (register `python3-ruamel.yaml` as a controller preflight prereq), minimal scope first.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` → 44 ✅ / 10 ⚠️ / 2 ❌. Failures expected (dev02 shut off per `feedback_one_vm_at_a_time.md`).
- One unanticipated warning: ERPNext dev01 (https://dev01.iridium.blue) HTTP 502. Operator explained: had been running `bench start` manually, stopped it for an inspection, forgot to restart. Not a project issue.
- main at `9318b11`. Working tree carried two staged-but-uncommitted session-log files from prior session (2026-05-02 1049). Operator authorized commit-on-main as `docs:` housekeeping before branching.
- 30 open issues at session start.

## What ran

### Pre-branch housekeeping

1. **Committed prior session logs** as `7bffbd4` on `main` (`docs: 2026-05-02 1049 session minutes — Session 1 of 4 (Phase 5 design + #332 audit)`).
2. **Closed #332** as `not planned` with full audit rationale posted as the closing comment ([comment 4364488148](https://github.com/martinhbramwell/ESACP/issues/332#issuecomment-4364488148)). Reason: 2026-05-02 audit found the three "human_review_core_edit" files contain debug residue + vestigial pins, not customisations — V14's `git checkout -f` discards them harmlessly. The operator initially asked for the closing rationale to be more verbose than the original mechanism description; the closing comment now stands as the durable record.
3. **Filed #335** (U6 smoke test) — Frappe `(dt, fieldname)` deduplication when source-tree edit + `tabCustom Field` row coexist. Gates P2/P3 viability for U1 (Q-G choice). Two paths: Path A (file + run as Session 2.5 before Session 3), Path B (accept P1-by-default, U6 moot). Operator picked Path A.

### #326 — `chore(preflight): register python3-ruamel.yaml as controller prereq` (PR #336)

Branch: `chore/check-tools-ruamel-326`. Merged via PR #336, merge commit `a3aa241` at 2026-05-02 18:49Z.

**Scope corrections during entry**:

- The agenda's "minimal first" recommendation (add `("ruamel.yaml", "python3-ruamel.yaml", "apt")`) was mechanically incompatible with the existing schema — `shutil.which("ruamel.yaml")` always returns None for a Python library, so the row would always show `[MISSING]` regardless of installation state. Schema extension was the smaller-than-minimal path here.
- Enumerated three mechanisms (α schema extension / β parallel list / γ hard import), then **escalated the choice to the operator unnecessarily**. Operator reframed as "would the business owner care which one?" → no. Picked α and proceeded. Existing rule `feedback_enumerate_mechanisms_before_committing.md` already covers this; no new memory written.
- Inlined the apt-py-vs-CLI detection branch (instead of a `_is_present` helper) to keep `check_tools.py` under its 68-line ratchet baseline. Vestigial `TaskResult` import dropped from `check_tools.py` (only `__init__.py` uses it; imported there directly from `common.types`).

**Final shape** (3 files, +94 / -31):

- `tools/pipeline/stages/preflight/check_tools.py` (78 → 66 lines): kind enum extended to `apt-bin` / `apt-py` / `manual`; `python3-ruamel.yaml` registered as the first `apt-py`.
- `tools/pipeline/stages/preflight/test_check_tools.py` (new, 64 lines): three colocated tests — load-bearing apt-py negative case + apt-bin / manual regression after the rename.
- `tools/size_baselines.json`: ratchet auto-update.

**Acceptance**:

- `[MISSING] ruamel.yaml (python3-ruamel.yaml)` line surfaces at preflight when the package is absent — covered by `test_missing_apt_py_ruamel`.
- apt install recipe captured automatically: `python3-ruamel.yaml` lands in `missing_apt`, picked up by the existing `apt_install()` flow in `tools/cli/confirm_prerequisites.py`.
- Live `./tools/esacp.py confirmPrerequisites` emits `[OK] ruamel.yaml (python3-ruamel.yaml)` on this controller.
- Anti-spiral size check passes after compaction.
- PR opened, merged, `mergedAt` non-null before #326 closed (per `feedback_pr_merge_before_session_close.md`). Merge-hash comment posted on #326.

### U3 decision (es-EC → es) made durable

Operator decided this session: change the language code on the 7 retroactively-promoted translations from `es-EC` to `es`. Reason: empirical knowledge that V13 country-level translation resolution is unreliable; family-level resolves consistently. Originally only stated in conversation; **filed as #337** (`chore(phase-2): dispose of 24 staged promotion writes; 7 translations use language code 'es' (not 'es-EC')`) so the decision is durable independent of session minutes.

## Issues touched

| Issue | Action | Resolution |
|---|---|---|
| #326 | Closed completed | PR #336, merge commit `a3aa241` |
| #332 | Closed `not planned` | Full audit rationale as closing comment |
| #335 | Filed (NEW) | U6 smoke-test prerequisite for P2/P3 |
| #337 | Filed (NEW) | U2 disposition + U3 design decision (es-EC → es) |
| #336 | PR — merged |  |

Open-issue count: 30 → 29 (closed #332 + closed #326 = -2; opened #335, #337 = +2; net 0 close to actual count, then earlier #332 close → 29).

## Reminders for the operator

1. **U1 — Q-G strategic decision (P1 / P2 / P3)** — gates Session 3. Resolution depends on #335 verdict (Path A chosen).
2. **#335 — U6 smoke test** — must run on dev01 before Session 3 starts. Two outcomes: pass → Q-G stays open; fail → Q-G collapses to P1.
3. **#337 — U2/U3 disposition** — 24 staged Phase 2 promotion writes still in worktrees; 7 of those need `es` (not `es-EC`). Disposition before Phase 5 ships.
4. **U4 — audit over-eagerness for db-resident classes** — deferred (operator quagmire-call). Will resurface every audit run; not a V14 blocker. No issue filed per operator decision.
5. **U5 — 6 db-resident "noise" drifts in v14_patch_script bucket** — resolves naturally with U1/Q-G choice.
6. **dev01 502** — restart `bench start` when next using the dev01 site.
7. **Plan-lock holds**: Session 3 = Phase 5 implementation (after U1 decided); Session 4 = Phase 3 generalised G2.

## Memory updates queued

None. The α/β/γ over-escalation incident was already covered by `feedback_enumerate_mechanisms_before_committing.md`; adding a duplicate would be noise. The U3 decision is durable in #337, not a recurring rule.
