# 2026-05-21 1018 — Session 70 minutes

## Stated objective

Resume LSKB#15 (Plan-B Phase 4 substrate-apply for `sales_partner_commissions`) per S69 audit-end verdict (ESACP#400 closed, NO-DRIFT, Epoch 2 unblocked).

## Outcome — substrate-apply primitive landed; LSKB#15 empirical retry deferred to S71

Investigation surfaced that the May-15/S54 + May-16/S55 substrate-apply failures were **not** planning drift — they were caused by the runbook bypassing two existing protection scripts (`g1_seed_patch_log.py` + `g2_clear_fixture_custom_fields.py`). Both protections were already wired into Stage 7 `data_restore.sh` AND `BaRe/handleRestore.sh @ 45b8775` as defense in depth; the hand-rolled raw `bench restore` + raw `bench migrate` on dev02 bypassed both layers.

Filed as ESACP#418 — *"bug(pipeline): no one-command path for substrate-apply test workflow — May-15 LSKB#15 failure was a packaging gap, not a code defect."*

Code landed in PR#422 (`feat/418-substrate-apply-primitive`):

| Deliverable | Path | Lines | Cap |
|---|---|---:|---:|
| IoC primitive | `tools/pipeline/orchestration/substrate_apply.py` | 64 | 80 |
| Thin CLI dispatcher | `tools/cli/apply_substrate_migration.py` | 38 | 80 |
| Colocated tests (4/4 pass) | `tools/pipeline/orchestration/test_substrate_apply.py` | 80 | 80 |
| Discoverability catalogue | `tools/vm_scripts/README.md` | 45 | — |
| Subcommand registration | `tools/esacp.py` | 106 | 150 |
| Architecture doc | `tools/CLAUDE.md` | +2 / −1 | — |

`esacp.py` held exactly at baseline 106 (docstring compressed 9→5 lines to absorb +4 for the new DISPATCH + VM_COMMANDS + add_subparser entries).

Sibling commit on LogiSoluMemory `main` (`ca5e1bd`): `feedback_substrate_workflow_named_primitive.md` + MEMORY.md index entry under "Critical Rules — Operations." Discipline rule: *"For any lab substrate operation, go through a named primitive in `tools/pipeline/`. Raw bench commands at an SSH prompt are a discipline violation, same severity as `wip/*` branches or commits without `fixes #N`."*

## Operator decision

S70 closes here. Empirical acceptance — destroy + rebuild dev02 substrate, install `sales_partner_commissions` at `5567c47`, invoke `./tools/esacp.py applySubstrateMigration dev02`, verify `bench migrate` exits 0 + all 18 SI Custom Fields present — deferred to S71 as its own dedicated session due to multi-hour wall-clock + hard-to-reverse blast radius of the dev02 rebuild. ESACP#418 stays open; LSKB#15 cross-repo close gates on the S71 empirical pass.

## Investigation timeline (mid-session)

1. Read [`LSKB#15`](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15) S47/S54/S55/S56 comments → established that paused at fixtures-import on `forma_de_pago_preferida` collision; S56 reframed as DocField-vs-CustomField drift; institutional fix in BaRe `45b8775` + g2.
2. Probed dev02 → `REMOTE HOST IDENTIFICATION HAS CHANGED` (host key differs from S55); substrate has been rebuilt or restored; S55 carry-forward state (`/tmp/lskb15-S55-migrate*.log`, `PATCHLOG00570`, SPC at `5567c47`) is almost certainly stale. Did NOT clear known_hosts mid-session per "Confirm before acting" rule (operator deferred dev02 work to S71).
3. Read `LogiSoluMemory/project_cesri_modules_fixture_bugs.md` Bug 3 → confirmed institutional fix design + GH#96 lineage (2026-04-04).
4. Read `BaRe/handleRestore.sh @ 45b8775` → confirmed conditional g1/g2 invocation at lines 355-364 (defense in depth) + bench migrate at line 368 inside the wrapper.
5. Read `tools/vm_scripts/g2_clear_fixture_custom_fields.py` → confirmed generic mechanism (scans `apps/*/*/fixtures/custom_field.json`, deletes both `tabCustom Field` + colliding `tabDocField` rows).
6. Read `tools/pipeline/stages/stage_7_data_restoration/data_restore.sh` → confirmed pipeline integration (E1 g1 pre / G `BaRe/handleRestore.sh` wrapper / G1 g1 again / G2 g2 + re-migrate).
7. Read `internal_docs/SessionLogs/2026-05-15-1147-session-minutes.md` (S54) → confirmed Step 5 ran raw `bench --site dev02.iridium.blue --force restore` (NOT `bash BaRe/handleRestore.sh`); Step 6 ran raw `bench --site dev02.iridium.blue migrate`. Both bypassed g1+g2.

Root cause: LSKB#15-style "apply a new bespoke-app migration on already-restored production data" has no narrower pipeline primitive than Stage 7's full first-time-provision sequence. Operator hand-rolled. Hand-rolled bypassed the institutional protections. Two cascading failures (ESACP#398, ce_sri#10) followed. Audit verified planning soundness; this issue closes the execution-discoverability layer.

## Fix design

Three coordinated deliverables in one PR (per `feedback_no_decision_theatre_on_clerical_work.md`, not three siblings):

1. **Substrate-apply primitive** — `tools/pipeline/orchestration/substrate_apply.py` bundles rsync `vm_scripts` → run g1 → run g2 → `bench migrate as ERP_USER`. IoC shape: `(config: Config, emit: Emit) -> TaskResult`. Stage 7 untouched.
2. **Discoverability** — `tools/vm_scripts/README.md` indexing every g\*/h\*/u\* protection script + its failure class + its current invocation sites. Reading this file first prevents the bypass shape.
3. **Discipline rule** — `LogiSoluMemory/feedback_substrate_workflow_named_primitive.md`; indexed in MEMORY.md.

Operator question at issue framing: *"Should we expect it to reappear?"* Answer codified into the discipline rule: the specific bypass cannot recur once the primitive exists; the class of failure (protection exists, not wired to this workflow) can recur in other costumes unless three structural defenses are added — (a) session-start question naming the pipeline primitive any restore/migrate work will go through, (b) feedback-memory rule banning raw bench at SSH prompts, (c) discoverable index of protections. Defenses (b) and (c) landed in this PR; (a) is operator-pattern-level, not enforceable mechanically yet.

## QA verdicts

| Trigger | Invocation | Verdict | Notes |
|---|---|---|---|
| T1 (pre-commit) | `Agent(esacp-qa)` mid-session, pre-`d676318` | `approve-with-conditions` / `hard_block:false` | Condition applied: drop `fixes martinhbramwell/LogiSoluKnowBase#15` from commit body — cross-repo auto-close must not fire before empirical proof. Architecture caps + IoC + tests-colocation + no-tenant-detail + Conventional Commits + GPG all verified by QA. |

T2 (pre-merge) and T5 (pre-issue-close) will fire in S71 once empirical acceptance passes and PR#422 is ready to merge / LSKB#15 ready to close. T3 (pre-push) on the session-close commit is rolled into the close-batch row below (§2.1 combined). T4 (pre-destroy) does not apply this session (no destructive ops).

## GitHub issue activity

| Issue | Action | Why |
|---|---|---|
| ESACP#418 | filed (open) | Bug found — packaging gap, three-deliverable fix design |
| ESACP#418 | pointer comment posted | S70 close status + landed deliverables + S71 carry |
| LSKB#15 | pointer comment posted | Substrate-apply primitive landed; empirical retry path documented |
| PR#422 | opened against `main` | Code + tests + discoverability + arch doc; acceptance gates on S71 empirical proof |

LogiSoluMemory commit `ca5e1bd` pushed to `main` directly (memory repo convention).

## Counts at session end

- ESACP open: **45** (was 42 at S70 start; +#418 + Junior's #415 +#416). The 3 net additions are all legitimate.
- LSKB open: **9** (unchanged).
- ce_sri open: **6** (unchanged; #10 remains gated on the PR#422 empirical pass — closeable as "covered by institutional fix" after, or kept open as parallel hygiene track; operator call post-merge).
- ce_sri_svc open: **2** (unchanged).
- LogiSoluValidations open: **2** (unchanged).
- BaRe open: **2** (unchanged).
- `sales_partner_commissions/main`: `5567c47` (unchanged, S47 onward).
- `tools/esacp.py`: 106 lines (baseline held).

## TRIVIAL_FIXES.md status

Unchanged. 3 monitor-only entries (LogiSoluMemory Trigger 3 skip pattern S33; `tools/secrets.py +x` S47; `sync_check.sh:2 Mighty` S58).

## Carry-forward operator-reminders (delta)

- **NEW (S70)**: ESACP#418 empirical acceptance — destroy + rebuild dev02, install SPC at `5567c47`, run `./tools/esacp.py applySubstrateMigration dev02`, verify acceptance criteria. Multi-hour. Own session (S71).
- **NEW (S70)**: PR#422 merge gates on the empirical pass. Add `fixes martinhbramwell/LogiSoluKnowBase#15` to the PR body / a follow-up commit only after empirical pass (per QA T1 verdict condition).
- **dev02 host key changed since S55** — known_hosts entry will need pre-clearing before S71 work. Follow `feedback_known_hosts_preclear.md` (preclear by hostname AND IP).
- **LSKB#15 cross-repo close** — gates on the S71 empirical pass via PR#422. Do NOT add the `fixes` keyword to PR#422's commit until the empirical test runs cleanly.
- LSKB#15 build-evidence (`/tmp/lskb15-S55-migrate*.log` on dev02) is almost certainly stale — host key changed. Treat as gone; fresh evidence captured in S71.
- **ce_sri#10** — block-chain transferred. Was: gated on ESACP#400 (closed). Now: covered-by-PR#422 institutional fix. Operator call post-merge: close as "covered by institutional fix" or keep open as parallel hygiene.

(Carry-forward items from S69 next-agenda that did not change in S70: `on_boarding` branch handoff, LogiSoluMemory cross-repo cleanup, ESACP#401 + dev02 intermittents, LSKB#11 / #16 / #18 / #21, ESACP#387 / #394 / #395 / #396 / #397, ESACP#383 / #361, TRIVIAL_FIXES entries, MariaDB-10.6 PS=OFF Packer note, T3-miss S58 monitor, post-#400 audit Stage-6-equivalent every ~50 closes — all unchanged.)

## Operator decisions to honor (carry forward)

All S69 decisions carry. No new decisions to log; deferral of dev02 empirical work to S71 is a scheduling micro-decision, not a substantive carry.

## SESSION END audit — four steps

1. **Forward-tense** — all in-session commitments executed: ESACP#418 filed and pointer-commented; PR#422 opened; LSKB#15 pointer-commented; LogiSoluMemory commit pushed; ESACP branch pushed; QA T1 verdict obtained and condition applied; tasks tracked end-to-end. Deferred items (empirical proof, dev02 rebuild) explicitly carry to S71 with operator authorization.
2. **GH issue references** — ESACP#418 (filed + commented), LSKB#15 (commented), PR#422 (opened with full body + test plan). All within-session.
3. **PRs opened** — PR#422 opened but **NOT merged** this session — empirical acceptance is the merge gate, deferred to S71. Per `feedback_pr_merge_before_session_close.md`, this is OK because the PR isn't claimed merged; #418 stays open accordingly.
4. **Unresolved doubts** — operator explicitly deferred dev02 work to S71 in writing; no other unresolved doubts.

## Self-classification

Substantive-class session under 1:1:1 discipline. Single issue (#418), single branch (`feat/418-substrate-apply-primitive`), single session — with the explicit understanding that the empirical acceptance test runs in S71 on the same branch (NOT a new issue, NOT a separate scope). The branch stays open; the issue stays open; the work continues in S71.

Under the S69 mechanical introspection-sidebar trigger (CLAUDE.md / `feedback_umbrella_branches.md`): this session does NOT touch MEMORY.md *indexing* (only adds one line under existing "Critical Rules — Operations"), but DOES attrite one carry-forward item (LSKB#15 substrate-apply path identification deferred from S69 — discharged via #418). The diff-based trigger reads as marginal; the session shape is clearly substantive-feature (new primitive, tests, PR), not sidebar. Classification: substantive, not sidebar.

## Staged files for session-close commit

- `internal_docs/SessionLogs/2026-05-21-1018-session-minutes.md` (this file)
- `internal_docs/SessionLogs/2026-05-21-1018-next-agenda.md` (S71)
- `internal_docs/qa-log.md` (S70 close-batch row)
