# 2026-06-08 1424 — Session 113 minutes

> Objective: **#660 — eliminate snapshot masking at the 3 remaining sites + de-dup
> `take_baseline_snapshot` onto `create_snapshot`/`snapshot_or_raise`.**
> Outcome: **DONE** — PR #668 squash-merged to main (`db4365b`); #660 CLOSED. First substantive
> change to land *with the new #663 test gate verifying it end-to-end*; suite 61/61 green (CI 11s).

## What happened

**#660 — the snapshot-masking root-cause neighbourhood (the objective).**
#658 (S111) hardened the two provision-macro *final* snapshots and added retry inside
`create_snapshot`, but the same masking class persisted at **3 more sites** it deliberately scoped
out to keep its 1:1:1. This session closed all three, each with an explicit fatality decision:

| Site | Before | After |
|---|---|---|
| `stage_1_vm_creation/baseline_snapshot.py` | copy-paste raw-virsh `subprocess`, warned-and-returned-None — bypassed the #658 retry **and** failure propagation, for the very Baseline that `verify.check_baseline_snapshot` keys on | delegates to `snapshot_or_raise` (retry-backed single source of truth); **raises** RuntimeError on failure, matching the stage-1 unit contract (`virt_install`/`clone_template`/`wait_ssh` all raise). Raw subprocess **deleted**. |
| `ansible_provision.py` "Fresh Install" (pre-provision, legacy path) | bool return discarded | **best-effort by explicit decision** — a rebuild speed-up, not the gate key; now acts on the return with a non-fatal note and continues |
| `ansible_provision.py` "Baseline" (post-ansible, legacy path) | bool return discarded | **fatal** — `return False` on failure (matches `provision_vm`'s existing bool contract; CLI exits non-zero) instead of phantom-succeeding |

**Failure-contract analysis drove the design.** Stage-1 units signal failure by `raise RuntimeError`
(`run_stage_1` does not catch — propagates to the runner), so `take_baseline_snapshot` delegating to
`snapshot_or_raise` is contract-correct. The legacy `provision_vm` path uses a bool-return contract
(SSH-unreachable and playbook-fail both `return False` → CLI exit 1), so the post-ansible Baseline
fix uses `return False`, not `raise` — consistent with the function it lives in.

**Tests (under the #663 gate).** Two new colocated test files:
- `stage_1_vm_creation/test_baseline_snapshot.py` — delegates-to-`snapshot_or_raise` (with the
  hypervisor alias so it still runs over SSH), failure-propagates, and a `test_no_raw_subprocess`
  source guard that the virsh duplication stays deleted.
- `orchestration/test_ansible_provision.py` — Baseline-failure-is-fatal, Fresh-Install-failure-is-
  best-effort, happy-path.

## Verification (acceptance)
- **61/61 green** via `./tools/run_tests.py` (was 59 — +2 new files), locally and on main post-merge.
- **CI `run-tests` PASS in 11s** on a clean GitHub runner — the authoritative acceptance.
- `pre_commit_size_check.py` exit 0; `pre_commit_exec_check.py` exit 0; both new tests at index `100755`.
- Acceptance (#660): no snapshot creation discards success/failure silently ✅; `take_baseline_snapshot`
  routes through the primitive ✅; a forced stage-1 baseline-snapshot failure fails the stage loudly ✅.

## Size ratchet
- `ansible_provision.py` baseline `size_baselines.json` 55→63 (justified error-handling growth, under
  the 80-line pipeline cap) — updated manually.
- `baseline_snapshot.py` auto-ratcheted 22→21 (shrank after the raw impl was replaced).

## Operator decisions this session
- Pin the recommended objective **#660** (the clean 1:1:1 continuation of #658).

## QA verdicts
- **Pre-commit (Trigger 1)**: esacp-qa **approve** — fatality classification correct, dead virsh
  duplication deleted in the same commit, tests at `100755`, caps satisfied.
- **Pre-merge (Trigger 2)**: esacp-qa **approve** — T2 advisory carve-out (prior T1 approval, no new
  commits, clean merge); 1:1:1 + `fixes #660` for auto-close confirmed.

## Issues closed this session
- **#660** — auto-closed via `fixes #660` on the squash-merge of PR #668.

## Session-close audit
Clean. #660 CLOSED via `fixes`; PR #668 `mergedAt` non-null (`2026-06-08T18:22:17Z`); acceptance
proven green in CI; no behavioural lessons requiring memory writes; no unresolved operator concerns.
No issues filed this session.

## End state
- **main tip**: `db4365b` (S113 squash-merge of PR #668; #660 closed).
- **Kept branches** (no prune): `feat/660-snapshot-masking-sites` (merged), plus prior S110–S112 set.
- **Open issues**: ESACP **87** (start-88, −1 closed, 0 filed), LSKB **13**.
- **VMs**: saconsole + dev15_01 (Ubuntu 24.04) running; dev01/dev02 shut off by design.
- **sync_check**: 4 expected FAILs (dev01/dev02 down by design); §18 suite green (now 61/61).
- **Working tree**: clean apart from Junior's untracked `on_boarding/onBoardingQRcode.png` (left).
