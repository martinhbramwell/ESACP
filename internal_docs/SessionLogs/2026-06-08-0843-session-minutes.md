# 2026-06-08 0843 — Session 111 minutes

> Objective: **#658 — `create_snapshot` masks failures + transient final-snapshot retry.**
> Outcome: **DONE** — PR #661 merged to main (`6f3cd7c`), #658 closed. Plus a procedural-integrity
> investigation (operator-prompted) that surfaced a missing test-execution gate and filed the
> root cause + three symptoms.

## What happened

**#658 — snapshot masking + transient retry (the objective).**
- Root cause confirmed from the issue's S110 correction comment: not a 24.04 incompatibility — two
  pre-existing bugs. (a) `snapshot_ops.create_snapshot` returned `False`, but both provision macros
  discarded the return and reported "complete" → a Baseline-less VM looked like a successful build
  (breaks idempotency gate / rollback / self-repair; violates no-masking). (b) the final snapshot
  fails transiently right after heavy I/O (`Extra element disks in interleave`, libvirt 6.0.0) and
  self-resolves in seconds.
- Fix: `create_snapshot` now retries (3×, 3s backoff) before returning `False` — root-cause fix, all
  callers benefit. New `snapshot_or_raise()` wraps it and raises `RuntimeError` on failure (shared
  raise-policy; DRY). Both `macro/provision.py` + `macro/provision_generic.py` call it for the final
  snapshot → a failed snapshot now FAILS the provision loudly.
- Colocated `test_snapshot_ops.py`, 4/4 pass: retry-then-success, exhaustion→`False`,
  no-sleep-on-first-success, raise-is-fatal. Accepted on unit-test acceptance; live provision run
  explicitly waived by operator.
- Size ratchet: refactored to keep both macros at baseline (no growth); `snapshot_ops.py` bumped
  39→75 in `size_baselines.json` (cohesive, under the 80-line cap); test recorded at 79.
- esacp-qa: approve at pre-commit, pre-push, and pre-merge. Squash-merged (`6f3cd7c`), branch kept
  (`feedback_keep_merged_branches`), #658 auto-closed via `fixes #658`.

**Scope discipline.** Mapping call-sites (root-cause rule) found the masking class at 5 sites, not 2.
The other 3 (`ansible_provision.py` ×2 + the duplicate `take_baseline_snapshot` that bypasses the
primitive) were deferred to **#660** to preserve 1:1:1 — not folded into this PR.

**Procedural-integrity investigation (operator-prompted).** A broad test sweep during the work showed
failures the operator correctly refused to let me wave off as trivial. Investigation found **one
systemic root cause: nothing in the project ever runs the test suite** (no test CI — only
`jekyll-pages.yml`; pre-commit runs only the size ratchet; `sync_check` runs no tests; no runner). So
colocated tests rot unseen. Three live instances: `test_hub_seed_iso` broke 4 days earlier via #583
(prod fine, test `_PARAMS` left stale — shipped to main); `test_hosts_map_remove` couples to the live
`hosts_map.yml` and collides with the now-real `dev01`; three test files committed non-executable
(violating invoke-as-executable). Filed root cause **#663** + symptoms **#664/#665/#666**.

**Persona-architecture decision (operator question).** On whether `esacp-qa` should be upgraded into a
full domain persona trained on GoF/CI-CD: decided **no** — keep `esacp-qa` a narrow, independent
read-only *referee* (its value is independence; #341); add a *separate* code-craft/architecture
critic as an advisory expert if/when built. Captured with full reasoning as sibling issue **#662**
(refs #536/#615/#341). The S111 test-gate gap (#663) named as that persona's natural first assignment.

## Issues filed this session
- **#660** — bug(pipeline): 3 remaining snapshot-masking sites + `take_baseline_snapshot` duplicates `create_snapshot`.
- **#662** — feat(meta/personas): add a code-craft/architecture critic; keep `esacp-qa` a narrow referee (decision record).
- **#663** — bug(ci): no test-execution gate; add discovery runner (run tests *as executables*) + CI/pre-commit wiring + exec-bit lint. **Root cause; load-bearing.**
- **#664** — bug(test): `test_hub_seed_iso` stale since #583 (`_PARAMS` missing `vm_user`).
- **#665** — bug(test): `test_hosts_map_remove` couples to live `hosts_map.yml` + real `dev01`.
- **#666** — bug(test): three colocated tests committed non-executable.

## Memories secured (LogiSoluMemory `fceafef`)
- `feedback_tests_with_code.md` — companion caveat: **colocation without execution = silent rot**; the
  three S111 instances; gate = #663; standing lesson "added a colocated test ≠ the test runs — re-run
  neighbour tests yourself until #663 lands." MEMORY.md index hook updated.

## Session-close audit
Clean. (Lesson durably homed in memory + pushed; all filings executed; PR #661 `mergedAt` non-null;
#658 CLOSED.)

## End state
- **main tip**: `6f3cd7c` (S111 squash-merge of PR #661, #658 closed).
- **Kept branches** (no prune): `feat/658-snapshot-no-mask-retry` (merged), plus prior S110 set.
- **Open issues**: ESACP **92** (start-87 +6 filed −1 closed), LSKB **13**.
- **VMs**: saconsole + dev15_01 (Ubuntu 24.04) running; dev01/dev02 shut off by design.
- **sync_check**: 4 expected FAILs (dev01/dev02 down by design); no real failures.
- **LogiSoluMemory**: clean, pushed (`fceafef`).
