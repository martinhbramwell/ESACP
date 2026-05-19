# Session Minutes — Phase 2A Pipeline Primitive Extraction (#206)

**Date:** 2026-04-21 ~21:00–21:36 EDT
**Branch:** `fix/206-snapshot-vm-subprocess` (merged to `main` via `858d631`)
**Issues closed:** #206, #275 (2)
**PR:** #279 — merged 2026-04-22T01:34:54Z
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md`; session entered at `main @ 9b4b4cf`

## Objective

Close #206 by extracting a `snapshot` pipeline-orchestration primitive
and rewriting `tools/cli/snapshot_vm.py` to call it, removing the last
`subprocess.run` from the dispatcher layer.

## Outcome

Objective met with a twist: no new primitive was needed. The existing
`tools/pipeline/orchestration/snapshot_ops.py` (added in Phase 7 #195)
already exposes `list_snapshots` and `create_snapshot` — the issue's
"create a new snapshot.py" fix-sketch predated that extraction. The
actual remaining work was rewiring the dispatcher to the primitive that
was already there. #275 was piggybacked because it blocked #206's own
grep-test acceptance criterion (see gate note below).

Open issues: **24 → 22** (−2, matching plan prediction for Phase 2A).

## #275 piggyback — gate rationale

#206's issue body specified this acceptance criterion:

> `grep -rn 'subprocess.run' tools/esacp.py tools/api.py tools/job_worker.py tools/cli/` returns only `_spawn_job` in api.py

That check could not pass while two SUT integration harnesses
(`tools/cli/verify_add_host.py`, `tools/cli/verify_provision_generic.py`)
were flagged as unexpected subprocess calls. Both call the built
`esacp.py` CLI under test — legitimate per
`memory/feedback_sut_frozen_tests_unlimited.md` — but `verify_phase7.py`
had no exception for them. They were pre-existing on `main @ 9b4b4cf`
(confirmed via `git stash` + re-run) and tracked as #275 (filed during
the 1830 session-close audit).

Options considered: (A) ship #206 alone, document the FPs as carried;
(B) add a one-line carve-out in `verify_phase7.check_no_subprocess()`
for `tools/cli/verify_*.py`. Chose B — tight coupling (#275 is the
natural dependency of #206's own grep acceptance), zero behaviour change
to any SUT, one logical line added.

## Per-issue work

**#206 (`snapshot_vm` subprocess violation)** — rewrote
`tools/cli/snapshot_vm.py` (29 → 27 lines):

- Dropped `subprocess` import and `SNAPSHOT_PY` path constant.
- Imports `tools.pipeline.orchestration.snapshot_ops` directly.
- `list` branch: `snapshot_ops.list_snapshots(vm)` → prints names
  one per line, or `(no snapshots on vm)` if empty.
- `create` branch: checks `list_snapshots()` first to preserve the
  prior "already exists → skip" semantics, then calls
  `snapshot_ops.create_snapshot(vm, name, emit=print)`. Returns
  0/1 based on its boolean result.
- Removed `tools/cli/snapshot_vm.py` from `verify_phase7.SUBPROCESS_EXCEPTIONS`.

**#275 (`verify_phase7` FP on SUT harnesses)** — added a filename-prefix
carve-out in `check_no_subprocess()`:

```python
if rel.startswith("tools/cli/verify_") and rel.endswith(".py"):
    continue
```

Rationale: these files are SUT harnesses that intentionally invoke the
built CLI as a subprocess. They are not dispatchers. The naming
convention (`verify_*.py`) is a stable shape — matches the existing
`verify_add_host.py`, `verify_provision_generic.py`, and will catch any
future harness added under the same pattern without needing individual
SUBPROCESS_EXCEPTIONS entries.

## Behaviour delta (intentional)

- **`snapShotVM <vm>` (list)**: output now names-only, one per line
  (previously the full `virsh snapshot-list` table with Name, Creation
  Time, State, Parent columns). Operators who want the full table can
  still run `python3 platforms/kvm/snapshot.py list <vm>` — that
  standalone tool is untouched.
- **`snapShotVM <vm> <name>` (create)**: output now
  `[OK] Snapshot '<name>' taken` (from `snapshot_ops.create_snapshot`'s
  emit). Previously `Taking snapshot…` / `✅ Snapshot … created`. Info
  content preserved; formatting differs.

The `platforms/kvm/snapshot.py` standalone script is intentionally
untouched. It remains the operator-facing tool referenced in
`docs/BuildOutProcedure.md` for revert/delete/start/state operations.

## Files changed

| File | Change |
|---|---|
| `tools/cli/snapshot_vm.py` | 29 → 27 lines; subprocess removed, calls `snapshot_ops` |
| `tools/verify_phase7.py` | Removed `snapshot_vm.py` exception; added `verify_*.py` SUT carve-out |
| `tools/CLAUDE.md` | Removed `#206 deferral` bullet; updated `snapShotVM` note |
| `docs/CLI.md` | Updated `snapShotVM` wiring note |
| `tools/size_baselines.json` | Auto-ratcheted by pre-commit hook (29 → 27) |

## Acceptance verification

- ✅ `./tools/verify_phase7.py` — 6/6 green (target caps + category caps
  + no-subprocess + help loads).
- ✅ `grep -rn 'subprocess.run\|subprocess.Popen' tools/esacp.py tools/api/ tools/job_worker.py tools/cli/`
  returns only `tools/api/jobs.py:37` (`_spawn_job` — #37) and the two
  carved-out `tools/cli/verify_*.py` SUT harnesses (#275). The
  `tools/cli/snapshot_vm.py` line is gone.
- ✅ `python3 -c "from tools.cli import snapshot_vm"` — imports clean.
- ✅ `./tools/esacp.py snapShotVM --help` — argparse unchanged.
- ⚠ Manual end-to-end snapshot smoke: **not feasible on controller**.
  Mighty has no local libvirt VMs (all VMs live on toshiba, reachable
  only via ProxyJump). The replaced code path had the same constraint —
  #206's "works end-to-end from CLI" acceptance bullet was inherited
  from an older architecture. Documented in the PR body.

## PR + merge

- Commit `d481dfe` on `fix/206-snapshot-vm-subprocess` (GPG-signed,
  verified). Pinentry succeeded first attempt this session.
- PR #279 opened with `fixes #206, fixes #275` in the body (comma
  syntax per `feedback_pr_fixes_comma_syntax.md` — both auto-closed on
  merge).
- Merged via `gh pr merge 279 --merge` (branch kept per
  `feedback_keep_merged_branches.md`). `mergedAt` = 2026-04-22T01:34:54Z.
- Merge commit: `858d631`. Local `main` fast-forwarded. Working tree
  clean.
- Auto-close: both #206 and #275 closed by GitHub at 2026-04-22T01:34:55Z.

## Plan update

`~/.claude/plans/open-issues-purge.md` Phase 2A row marked ✅ with the
revised exit count (23 → 22) and the note that #275 piggybacked because
of the acceptance-criterion dependency. Plan next hop: **Phase 2B**
(#211 — orphan audit of `tools/pipeline/orchestration/` files).

## State handed to next session(s)

- `main @ 858d631`, working tree clean.
- Phase 2A runtime verification: the snapshot CLI path now goes through
  `snapshot_ops`. Any future snapshot-triggering code that imports
  `snapshot_ops` gets the same behaviour. No pipeline runs touched.
- Plan next hop: **Phase 2B** (#211 — orphan audit). Verification:
  audit-only → delete/document; no matrix re-run. Expected delta: 22 →
  21.

## Reminders to user (unresolved concerns)

None live for this session. The GPG-agent `default-cache-ttl` carry
(previously resurfacing in the 1830 and 1801 minutes) has been moved
to `memory/feedback_gpg_agent_cache_ttl.md` + MEMORY.md "Operator
Environment" index line. It did not cost session time here (single
clean pinentry). Per the new memory file's own rule, future minutes
will only re-mention when it actively costs time.

## Session-close audit resolutions

- PR #279 `mergedAt` = 2026-04-22T01:34:54Z (non-null, DONE valid).
- #206 approach-divergence finding (no new primitive needed; existing
  `snapshot_ops.py` reused) posted as issue comment:
  <https://github.com/martinhbramwell/ESACP/issues/206#issuecomment-4292974641>
- #275 fix approach (prefix carve-out vs. per-file exceptions) posted
  as issue comment:
  <https://github.com/martinhbramwell/ESACP/issues/275#issuecomment-4292975097>
- GPG-agent carry → `memory/feedback_gpg_agent_cache_ttl.md` (new
  feedback memory) + MEMORY.md index (new "Operator Environment"
  section).

## File trail

- Phase 2A commit: `d481dfe` on `fix/206-snapshot-vm-subprocess`
- Merge commit: `858d631`
- PR: <https://github.com/martinhbramwell/ESACP/pull/279>
- Plan status edit: `~/.claude/plans/open-issues-purge.md` (Phase 2A ✅)
- MEMORY.md edits: open-issues line (24 → 22 + Phase 2A entry); new
  "Operator Environment" index section
- New memory file: `memory/feedback_gpg_agent_cache_ttl.md`
- Issue comments: #206#issuecomment-4292974641, #275#issuecomment-4292975097
- This minutes: `docs/SessionLogs/2026-04-21-2100-session-minutes.md`
- Prior-session minutes: `docs/SessionLogs/2026-04-21-1830-session-minutes.md`
  (Phase 1B repo/tooling sweep)
