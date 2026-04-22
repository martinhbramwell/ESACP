# Session Minutes — Phase 3B Saconsole Bundle (#220 ship, #225 close)

**Date:** 2026-04-22 ~15:30–19:00 EDT
**Branch:** `refactor/220-saconsole-decomposition` (draft PR, not merged)
**Issues closed:** #225 (won't-fix, mission-alignment)
**Issues in flight:** #220 (code committed, awaiting Run 01 acceptance)
**PR:** #287 (draft)
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md` Phase 3B; session entered at `main @ f294cde`

## Declared objective

Phase 3B of the open-issues purge plan — **saconsole bundle**:
decompose `bootstrap_hub.sh` (#220) and optimize saconsole backup
transport + right-size development-quadrant volumes (#225). Narrowed at
session start to transport-only on #225 (the issue's own text splits
transport from volume-sizing), with acceptance (Run 01 — live saconsole
destroy+rebuild) deferred to a follow-up session per operator
instruction.

## Scope decisions taken mid-session

1. **#284 / #285 parking** — approved at start, then explicitly deferred
   ("defer") — not actioned this session.
2. **#225 benchmarking before coding** — accepted. Ran the proposed
   two-stage transport against live `saconsole.qcow2` (34 GB) with
   saconsole up, torn reads OK for timing.
3. **Mission-alignment correction mid-session.** Benchmark findings
   invalidated the issue's hypothesis. Operator reframed the project's
   short-term priority as ERPNext V13 → V16, with "no outstanding
   issues" as the gate. #225 re-evaluated in that light: saconsole
   backup speed is operator convenience on a rare operation, not
   mission pain. Closed won't-fix.

## #220 — bootstrap_hub.sh decomposition (shipped, awaiting acceptance)

`platforms/kvm/bootstrap_hub.sh`: 425 lines → 65-line thin orchestrator
that sources 12 phase files under `platforms/kvm/bootstrap_hub/`:

| File | Lines | Role |
|---|---|---|
| `_helpers.sh` | 68 | `log` / `die` / `step` / `remote` / `vm_*` / `snapshot_*` / `take_snapshot` / `HUB_SSH_OPTS` / `ssh_ready` |
| `01_preflight.sh` | 27 | cloud-localds, SSH key, SOPS age key, hypervisor reachability, pool active |
| `02_build_seed.sh` | 19 | `cloud-localds` renders seed ISO from user-data + meta-data |
| `03_upload_seed.sh` | 16 | mtime-gated SCP to hypervisor |
| `04_create_vm.sh` | 40 | `virt-install` via SSH heredoc; idempotent on existing VM |
| `05_wait_ssh.sh` | 53 | autoinstall state-machine wait → SSH poll |
| `05b_wait_cloud_init.sh` | 18 | `cloud-init status --wait` on hub (GH #231 context) |
| `06_snapshot_fresh.sh` | 4 | `take_snapshot 'Fresh Install'` |
| `07_ansible_provision.sh` | 20 | `ansible-playbook site-kvm.yml --limit <hub>` via ProxyJump |
| `08_snapshot_baseline.sh` | 4 | `take_snapshot 'Stage 2.2 Baseline'` |
| `09_handoff.sh` | 72 | hub SSH pubkey → hypervisor authorized_keys, /etc/hosts, known_hosts, stale-key sweep |
| `99_summary.sh` | 35 | operator banner + next-step instructions |

All ≤ 100 lines. Behaviour preserved verbatim — phase boundaries,
idempotency checks, SSH options, snapshot names, ProxyJump semantics
all identical. `bash -n` clean on every file.

`tools/pre_commit_size_check.py` extended:
- `CHECKED_SUFFIXES` now `(".py", ".sh")`.
- `TARGET_LIMITS` gains `platforms/kvm/bootstrap_hub.sh: 100`.
- `CATEGORY_LIMITS` gains `platforms/kvm/bootstrap_hub/: 100`.
- Error message generalized beyond Python dispatchers.

Baselines recorded in `tools/size_baselines.json` — hook auto-staged
as usual.

`platforms/kvm/CLAUDE.md` updated to describe the new layout.

Commit: `06da8a6` (GPG-signed, RSA key `A232D66FDA9704E8`).

## #225 — closed won't-fix (mission-alignment)

Benchmarked the issue's two-stage proposal against live saconsole qcow2:

| Test | Result |
|---|---|
| Stage 1 — `virsh vol-download` hypervisor-local (no SSH) | 34 GB in 2m27s = **233 MB/s** ✓ |
| Stage 2 — `rsync --sparse` pull hypervisor → controller | 9.7 GB in 60 min = **2.7 MB/s** ✗ |
| Raw SSH, Mighty → toshy, 200 MB | 27 s = **7.4 MB/s** |
| Raw SSH, toshy → Mighty, 200 MB | 78 s = **2.56 MB/s** |
| `vol-download` output file sparseness | `du` = `ls` = 34 G — **dense** |

Root cause: the physical WiFi link from toshy to Mighty is capped at
~2.5 MB/s downstream. The `--sparse` flag is a no-op because the
`vol-download` output file is dense. The <15 min target for 34 GB
requires ≥38 MB/s sustained — not reachable on WiFi, not reachable on
100 Mb/s Ethernet, only on gigabit. The proposed transport measured
**worse** than what it replaced.

But the deeper problem: a 2.5 h backup on a rare deliberate rebuild is
operator convenience, not mission pain. The mission is an AI-maintainable
ERP for a family-owned business. Hub rebuild frequency × 2 h saved ≠
anything the business or the AI-maintenance loop feels. Closed with
measurement paste + reasoning.

The `rebuild_saconsole.sh` transport edit was reverted before commit —
it's not on the branch.

## Memory updates

- `memory/feedback_mission_priority_check.md` — new feedback memory:
  ask whether a perf ticket's pain serves the mission or is operator
  convenience before scoping. References this session's trap and
  cross-refs `feedback_not_perfection_project.md`.
- `memory/MEMORY.md`:
  - New "Short-Term Priority — ERPNext V13 → V16" section near the top,
    pointing at `project_upgrade_v13_to_v16.md` (currently a parked
    stub) as the plan to flesh out.
  - New Critical Rules line for `feedback_mission_priority_check.md`.
  - Open-issue count 19 → 18; #225 tagged closed won't-fix;
    `refactor/220-saconsole-decomposition` branch noted pending
    Run 01 + merge.

## Files changed

### On `refactor/220-saconsole-decomposition` (commit `06da8a6`)

| File | Change |
|---|---|
| `platforms/kvm/bootstrap_hub.sh` | 425 → 65 lines (thin orchestrator) |
| `platforms/kvm/bootstrap_hub/_helpers.sh` | NEW (68 lines) |
| `platforms/kvm/bootstrap_hub/01_preflight.sh` | NEW (27) |
| `platforms/kvm/bootstrap_hub/02_build_seed.sh` | NEW (19) |
| `platforms/kvm/bootstrap_hub/03_upload_seed.sh` | NEW (16) |
| `platforms/kvm/bootstrap_hub/04_create_vm.sh` | NEW (40) |
| `platforms/kvm/bootstrap_hub/05_wait_ssh.sh` | NEW (53) |
| `platforms/kvm/bootstrap_hub/05b_wait_cloud_init.sh` | NEW (18) |
| `platforms/kvm/bootstrap_hub/06_snapshot_fresh.sh` | NEW (4) |
| `platforms/kvm/bootstrap_hub/07_ansible_provision.sh` | NEW (20) |
| `platforms/kvm/bootstrap_hub/08_snapshot_baseline.sh` | NEW (4) |
| `platforms/kvm/bootstrap_hub/09_handoff.sh` | NEW (72) |
| `platforms/kvm/bootstrap_hub/99_summary.sh` | NEW (35) |
| `platforms/kvm/CLAUDE.md` | note new layout |
| `tools/pre_commit_size_check.py` | +18, `.sh` support + new category |
| `tools/size_baselines.json` | +13 baseline rows |

### On `main` (this minutes commit)

`docs/SessionLogs/2026-04-22-1903-session-minutes.md` + updates to
`memory/*` (which live outside the repo in `~/.claude/projects/.../memory/`).

## Acceptance verification

- ✅ `bash -n` clean on orchestrator + every phase file.
- ✅ `tools/pre_commit_size_check.py` passes on staged diff.
- ✅ `sync_check` green at session start (46 ✅ / 11 ⚠ / 0 ❌).
- ✅ GPG-signed commit `06da8a6`.
- ✅ PR #287 opened as draft.
- ✅ #225 closed won't-fix with measurement paste.
- ⚠ **Run 01 (live saconsole rebuild) deferred** — #220 does not close
  until PR #287 merges after acceptance passes next session.

## State handed to next session

- `main @ <this minutes commit>`.
- `refactor/220-saconsole-decomposition @ 06da8a6` pushed, PR #287 draft.
- Open issues: **18** (net −1 from #225 close).
  #48, #65, #138, #153, #156, #157, #187, #202, #219, **#220** (in PR),
  #223, #235, #240, #241, #278, #280, #284, #285.
- Short-term priority: **ERPNext V13 → V16** with SRI / QR bottles /
  delivery routes / bespoke customizations. Gate: zero open issues.
  Plan file `project_upgrade_v13_to_v16.md` is a parked stub and needs
  fleshing out as the active plan.

## Reminders to user (unresolved concerns)

1. **Run 01 acceptance session** — next time there's a natural window to
   destroy + rebuild saconsole, exercise the decomposed
   `bootstrap_hub.sh`. PR #287 then marks ready-for-review; merge closes
   #220. Expect ~30–60 min plus whatever backup time the current WiFi
   link imposes.
2. **#284 / #285 still parked** — deferred per operator instruction this
   session; the V13 wizard temperament remains a V14-revisit item.
3. **Other 17 open issues** — each deserves its own mission-alignment
   pass before any more scope-reshuffling. The purge plan
   (`~/.claude/plans/open-issues-purge.md`) is now stale — Phase 3B's
   bundle assumption collapsed, and the V13 → V16 priority reset the
   frame. Worth re-drafting the purge plan against the new priority
   before picking the next issue.
4. **`project_upgrade_v13_to_v16.md` is a stub.** The V13 → V16 arc
   needs a real plan file (scope, approach, test strategy, sequencing)
   before any code work on it. Suggest a dedicated planning session.

## File trail

- Commit: `06da8a6` on `refactor/220-saconsole-decomposition`
- PR: <https://github.com/martinhbramwell/ESACP/pull/287>
- Closed: <https://github.com/martinhbramwell/ESACP/issues/225>
- New memory: `feedback_mission_priority_check.md`
- Updated memory: `MEMORY.md` (short-term priority + critical rules + issue ledger)
- This minutes: `docs/SessionLogs/2026-04-22-1903-session-minutes.md`
- Prior session minutes: `docs/SessionLogs/2026-04-22-1418-session-minutes.md` (Phase 3A wizard bundle)
