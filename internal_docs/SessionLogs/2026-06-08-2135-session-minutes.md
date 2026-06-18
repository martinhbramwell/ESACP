# 2026-06-08 2135 — Session 114 minutes

> Objective (pinned): **#655 — host-RAM preflight guard on the template-build path** (the S110 OOM root cause).
> Outcome: **DONE** — PR #669 squash-merged (`5c42992`); #655 CLOSED.
> Operator then directed a **Track-A housekeeping add-on**: **#653 — permission-prompt allowlist** —
> DONE, PR #670 squash-merged (`4554b37`); #653 CLOSED. Two objectives this session by explicit
> operator direction (substantive 1:1:1 + a single-issue housekeeping bundle, separate branches).

## What happened

### #655 — build-path RAM guard (the objective)
`/api/vm/{host}/start` already guarded VM start via `memory_guard.check_memory()`, but the
template-build path (`build_template.py` → `build.sh` raw `virt-install`, 4 GiB build VM) had **no**
check — so a build could oversubscribe the hypervisor and OOM-kill saconsole (the hub), which is
exactly what happened in S110.

- **`memory_guard`** — added `check_memory_for_ram(hypervisor, needed_kib, label)`: the build VM is
  not yet a defined domain, so the caller supplies the RAM rather than querying a `dominfo`. Existing
  `check_memory()` now delegates to it (reads the target's Max memory, then calls the shared core).
- **Anti-spiral split** — the refactor pushed `memory_guard.py` to 87 lines (over the 80 pipeline cap),
  so the pure parse/format helpers were extracted to a new **`memory_guard_parse.py`** (38 lines).
  `memory_guard.py` auto-ratcheted 77→58.
- **`build_template`** — preflight `check_memory_for_ram(DEFAULT_HYPERVISOR, 4096*1024, "packer-build")`
  **before** rsync/launch; raises a clear `RuntimeError` (running domains + free RAM) if it won't fit
  under the 2 GiB host reserve. Passes `--build-ram 4096` to `build.sh` so `build_template` is the
  single source of the build VM RAM; `build.sh`'s `BUILD_VM_RAM=4096` is now the documented hand-run
  fallback (new `--build-ram` arg arm).
- **Test** — `test_memory_guard.py` (colocated, 5 cases): the exact S110 oversubscription topology
  (15 GiB host, saconsole 4 + dev01 3 + dev15_01 6 + build 4 = 17 > 13 available → rejected), no-mask
  on `nodeinfo` SSH failure, and the `check_memory` delegate path. Suite **62/62** green.
- **Size ratchet** — `build_template` 52→66 hand-bumped (justified growth, under the 80 cap; precedent
  `ansible_provision` 55→63); `memory_guard_parse` new at 38.

### #653 — session-housekeeping permission allowlist (Track-A add-on)
Routine session-close edits (SessionLogs minutes/agendas, the close-audit hook, memory-dir files) hit
4–5 interactive permission prompts per session with no safety benefit. Fix splits by durability:
- **Checked-in `.claude/settings.json`** (shared, project-relative): `Edit/Write internal_docs/SessionLogs/**`,
  `Edit .claude/hooks/session_close_audit.sh`.
- **Local `.claude/settings.local.json`** (gitignored, controller-specific encoded memory-dir path):
  `Edit/Write` the LogiSoluMemory mount — added out-of-band, not committable.
- No blanket `Edit(**)`; `tools/pipeline/**` / ansible / SOPS still prompt. **Acceptance deferred to
  next session start** — permission rules load at startup; validate the no-prompt behaviour at S115.

### Track-A scope correction (honest finding)
The proposed Track-A "sweep" (#653, #614, #434, #488) collapsed on inspection to **#653 only**:
- **#614** — its acceptance test is a *mechanical pre-commit hook* (code = substantive), so closing it
  on a doc alone would breach acceptance-test-required. Stays open as substantive.
- **#434, #488** — *deferred trackers* (close only when upstream `gh` is fixed / hosts become
  public-reachable). Not closeable now.
- Lesson for the lined-up sweep: the small-issue backlog is mostly **substantive same-class code**
  (size-cap refactors #580/#581/#578/#452/#594), which belong under an **umbrella branch**, not a
  housekeeping bundle.

## Counts / state
- ESACP open: **87 → 85** (−2 closed: #655, #653; 0 filed). LSKB: **13**.
- main tip: `4554b37`. Kept branches (no prune): `feat/655-build-memory-guard`, `chore/653-permission-allowlist` (both merged).
- VMs: saconsole + dev15_01 running; dev01/dev02 shut off by design. Junior's `onBoardingQRcode.png` untracked, never staged.
- sync_check at start: 46✅/11⚠/4❌ — the 4 ❌ are dev01/dev02 shut-off (by design); §18 suite 61/61 (now 62/62 with the new test).

## Diff-based introspection-sidebar trigger: NEGATIVE
No MEMORY.md indexing change; no carry-forward attrition beyond the two closures. #653 is a single-issue
housekeeping bundle, not a sidebar.

## SESSION-END audit (4 prongs): clean
1. **Forward-tense** — all actions map to executed tool calls; "will confirm acceptance at S115" is
   durably homed in the #653 close comment + S115 agenda. No behavioural lesson requiring a memory file.
2. **GH refs** — #655 + #653 each stamped with their squash-merge hash; #654/#480-children surveyed for
   the strategic status (read-only, no new findings to post).
3. **PRs** — #669 `mergedAt` 19:23:04Z, #670 `mergedAt` 21:33:53Z — both non-null verified.
4. **Operator doubts** — the strategic "are we still on VM-rebuild plumbing / how many sessions to
   V15-V16 testing" concern is answered in the session report and carried into the S115 agenda framing.
