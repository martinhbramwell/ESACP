# Migration Plan — bespoke tenant V13 → V15 → V16

> **READ THIS FILE FIRST, every session.** It is the session protocol for the
> migration push. At session end, edit the relevant step with *how the task was
> completed* and commit its **durable proof artifact** (see "Proof method").
> This file is the route; **the acceptance suite is the law.**

---

## The one definition of success (the sole arbiter)

The migrated **V15** and **V16** systems must reproduce **all of the bespoke
tenant's functionality, giving the same or better results** — reached by a
**clean, automated run** (no hand-hacking). Nothing else decides done/not-done.
Substrate is disposable VM copies; **production is never in reach.**

### The recorded structural-vs-functional split — DO NOT re-ask (decided S10, 2026-05-05)

The operator already triaged the customisation surface into two check methods.
This is persisted in `LogiSoluValidations/README.md` + the catalogue's
`suite_section` / `audit_verdict` fields. Quoted, not paraphrased:

> *"SQL/fixture audits catch **structural** drift; this suite catches
> **behavioural** drift."*

| Check method | Surface (operator-assigned) | Tool |
|---|---|---|
| **Structural** | property setters, custom fields, custom docperms, translations, in-place core edits, print formats — *"explicitly NOT on the staffer list"* | `tools/customisation_audit/` A/B vs `customizations_catalogue.yml` |
| **Behavioural (functional)** | staffer workflow sections **A–H** (SRI sales-invoice, returnable Stock Entry, delivery-trip binding, sales-partner commission) — the **22 catalogued entries** that are *"the V14-migration behavioural test surface"* | `LogiSoluValidations` Playwright specs, bound by `suite_section` |

- **Structural is the runnable per-leg bar** (mechanical, complete today).
- **Behavioural is operator-paced** (specs grow as staff record) — it deepens
  confidence and is a **hard gate before the real production cutover**, not a
  per-leg blocker.
- "Same or better" is scoped to **bespoke**; stock V13→V16 changes (renamed
  routes, homepage rework, V14+ additions) are **not** failures (5-category
  method: `~/.claude/plans/v13-v16-schema-diff-report.md`).

---

## Proof method — durable proof of delivery (mandatory, every step)

A step is **DONE** only when all three hold:

1. **Concrete deliverable** exists — a named artifact (code merged on the branch,
   a generated report, an updated catalogue), never a description.
2. **Durable proof committed** — the step's proof **command + its actual output**
   is captured to `internal_docs/migration_proofs/<step-id>.log` and **committed
   on the branch**. The command is re-runnable; the output is the receipt.
3. **Re-verified at pickup** — `tools/migration_status.py` (built in S0)
   **re-executes every DONE step's proof command** at session start and flags any
   that no longer pass. A DONE step whose proof regresses is reopened.

Proof commands must be **cheap probes** (HTTP 200, `SELECT COUNT`, an audit-delta
diff, a test exit 0) — never the expensive operation itself. The migration runs
once; its proof is checkable in seconds, forever.

The plan step records, on completion: the **deliverable**, the **proof command**,
the **`migration_proofs/<step-id>.log` path**, and the **commit hash + date**.

---

## Existing assets — DO NOT rebuild (re-grounded S118)

| Asset | Path | What it is |
|---|---|---|
| Staged-upgrade engine | `tools/pipeline/upgrade_v14/` + `tools/upgrade_to.py` (parametric `--target-version {14,15,16}`, S2) | `bench switch-to-branch` chain; V13→V14 trialed in **#428 (CLOSED)** |
| Protected migrate | `applySubstrateMigration` (`substrate_apply.py`, #418) | g1+g2 guards + `bench migrate`, full log (#447) |
| Post-migrate fixups | `apply_v16_post_migrate_fixups.py` (R1, R3, R8/#617) + #626 | catalogued V13→V15 / V15→V16-leg fixes |
| Structural A/B engine | `tools/customisation_audit/` (12 `discover_*`, `core_diff_*`, `delta_report`) | discovers + diffs + classifies bespoke customisations between two substrates |
| Baseline catalogue | `LogiSoluValidations/audit/customizations_catalogue.yml` (V13 from `PRODUCTION_20260404`) | enumeration of bespoke surface = the structural bar (22 individual entries + 12 summary blocks) |
| Functional suite | `LogiSoluValidations` (Playwright, staff-recorded; sections A–H) | behavioural A/B; nascent (~3✅/3⏳/~10❌, no committed specs yet) |
| Prod backup | `$BESPOKE_ROOT/ce_sri/BKP/` (`BACKUP.txt` → active dump) | real V13 tenant data (a copy) |

**Failed jump on record:** single-jump restore-V13-onto-V15 + one migrate dies on
`tabDocField.is_virtual` (V15 code two majors ahead of V13 schema) — **#687**.
The staged path below is why.

---

## Governance for this push (overrides CLAUDE.md until both end-products pass)

- **No 1:1:1, no agendas, no minutes.** One objective : one session, all on
  `migration/v13-v15-v16`. This file replaces the agenda/minutes ceremony.
- **Gates kept:** pre-commit size-check, exec-bit lint, the test gate (#663 — CI
  blocks a red suite). **Suspended:** per-commit `esacp-qa`, issue-ref
  requirement. `esacp-qa` runs **once** at the final merge-to-main.
- **Obstacles:** fix in-session, no issue — **unless** it is a defect in **shared
  code that outlives the migration** (one-line issue) or it genuinely **needs the
  operator** (stop and ask).
- **Snapshot before each mutating step** so every leg is repeatable.

---

## The sessions (short spine — legs may split if defects demand)

### S0 — Acceptance harness + V13 ground-truth + push-mode wiring
- **Objective:** make "where are we" mechanically checkable; stand up the clean
  **V13 + prod-data** source bench every leg starts from.
- **Deliverable:** `tools/migration_status.py` (session-start probe that runs the
  structural A/B, **prints the recorded structural/functional split + catalogue
  coverage**, lists each DONE step and re-runs its proof); CLAUDE.md push-mode
  banner pointing here; SessionStart hook wired; a V13 prod-data bench.
- **Tools available:** `customisation_audit`, `customizations_catalogue.yml`,
  `delta_report`, restore primitives, SessionStart-hook infra.
- **Tools lacking (build now):** `migration_status.py`; the banner; **fix
  hosts_map lookup drift.** *(Prose correction, S0a:* the drift is **only** in
  `upgrade_to_v14.py` — it read a flat `hosts[]` that matches nothing against the
  live `groups.kvm.<key>` structure, so the dispatcher exited 1 "not found" on any
  real host. `customisation_audit/runner.py`'s `groups.kvm.<host>` read was already
  structurally **correct**; it was DRY-routed through `host_identity.kvm_hosts()`
  for single-source-of-truth, not because it was broken.*) Both now resolve via
  `host_identity` (`resolve_kvm_host` / `kvm_hosts`).
- **S0 split (S0a, 2026-06-10):** S0 bundled bounded tooling with a heavyweight VM
  build, so it was split. **S0a — DONE** (tooling: `migration_status.py` + tests,
  the lookup-drift fix, SessionStart hook); proof `migration_proofs/S0a.log`.
  **S0b-bench — DONE** (2026-06-10): the V13 prod-data bench is **dev01**, not
  dev02 — dev02 has since been migrated to V16 (`16.18.3`); the clean V13
  prod-data substrate is dev01 (frappe `13.58.22`, real tenant data: 22,433
  Sales Invoices). Ran the structural A/B; **established** the baseline
  `migration_proofs/delta_report_dev01.json` (373 drifts); proof
  `migration_proofs/S0b.log`. (Host correction operator-approved 2026-06-10.)
- **Proof → `migration_proofs/S0a.log`:** `migration_status.py` runs offline and
  prints live catalogue coverage (22 entries / 0 confirmed / 20 TBD); colocated
  tests green; `upgrade_to_v14 --substrate dev02` resolves past host lookup.
- **Proof → `migration_proofs/S0b.log` (S0b-bench):** `test_baseline_dev01.py`
  asserts the committed `delta_report_dev01.json` carries the established
  structural class/verdict distribution — a **cheap, offline** probe per the
  proof-method rule (the SSH `--bench` audit is the expensive one-time generation,
  not the routine proof; it ran once to produce the committed baseline).

### S0b — Finish operator triage of the 22 behavioural entries  *(operator-involved)* — **DONE (S119, 2026-06-10)**
- **Outcome:** all 22 signed off one-at-a-time — 2 high / 6 medium / 14 wont_test;
  catalogue `operator_confirmed: true` + `business_relevance` + `triage_note` each;
  `drift_evidence_index.md` binds every drift to its document trail. Proof
  `migration_proofs/S0b-triage.log` (LSV commit 8bf3271).
- **Objective:** complete the per-item sign-off the S10 catalogue left mid-triage
  (`operator_confirmed: false`, `business_relevance: TBD` on all 22).
- **Deliverable:** updated `customizations_catalogue.yml` with **22 entries
  `operator_confirmed: true` + `business_relevance` filled**, committed to
  `LogiSoluValidations`. This finalises which behavioural specs the functional bar
  requires.
- **Tools available:** the catalogue, `gap_filler_probe.py`, README sections A–H.
- **Tools lacking:** none (data + operator confirmation).
- **Proof → `migration_proofs/S0b.log`:** `grep -c 'operator_confirmed: true'` = 22
  and `grep -c 'business_relevance: TBD'` = 0 in the catalogue; commit hash recorded.

### S1 — V13 → V14, automated, structurally A/B-clean — **DONE (2026-06-10)**
- **Outcome:** `./tools/upgrade_to_v14.py --substrate dev01` runs all 10 stages
  clean (migrate exit 0, HTTPS 200 + v14). Five pipeline defects fixed
  (#688/#331/#689/#690/#691 — never run end-to-end before). legacy_error_fixes
  homed in LSV (`audit/legacy_error_fixes`, commit 024253a). V13→V14 structural
  A/B: **LOST=0** (zero bespoke loss), +11 stock naming-series Property Setters
  (expected). 18 fixture-equivalent core edits recreated as owned DB
  customisations. Proof `migration_proofs/S1.log` (commit 2f24279).
- **Objective:** staged V13→V14 on the prod-data bench via `upgrade_to_v14.py`,
  one command, no manual steps.
- **Deliverable:** working `upgrade_to_v14` run on the bench + a structural-delta
  report (V13→V14) showing zero bespoke loss.
- **Tools available:** `upgrade_v14/` package, `applySubstrateMigration`, #428.
- **Tools lacking:** hosts_map wiring fix (S0); any V14 bespoke-app compat fixups surfaced by running.
- **Proof → `migration_proofs/S1.log`:** bench on `version-14`, migrate exits 0;
  `customisation_audit` V13→V14 delta = **zero bespoke-customisation loss** (only
  expected stock additions).

### S2 — V14 → V15, automated = **END-PRODUCT #1 (V13→V15)**, same-or-better
- **Objective:** generalize the staged leg to V15; apply V13→V15-leg fixups (#626,
  #617/R8, R3); automated V13→V15.
- **Deliverable:** parametric V15 switch leg (code) + automated V13→V15 run +
  structural-delta report (V13-baseline-vs-V15) + 3 probe outputs.
- **Tools available:** `upgrade_v14` pattern (generalize past hardcoded
  `version-14`), `apply_v16_post_migrate_fixups`, `customisation_audit`.
- **Tools lacking:** the parametric V15 switch leg; V15-specific fixups discovered by running.
- **Proof → `migration_proofs/S2.log`:** lands 15.x; `customisation_audit`
  V13-vs-V15 = **same-or-better** (no lost bespoke); 3 V15-leg probes pass on real
  data (#617 series increments, #626 server-script executes, R3 no PrintFormatError).

### S3 — V15 → V16, automated = **END-PRODUCT #2 (V15→V16)**, same-or-better
- **Objective:** extend the staged leg to V16; apply V15→V16-leg fixups (R1
  homepage, #618 workspaces, leaderboard); automated end-to-end.
- **Deliverable:** parametric V16 switch leg + automated run + structural-delta
  report (V13-baseline-vs-V16).
- **Tools available:** the parametric switch leg (S2), `apply_v16_post_migrate_fixups`,
  `customisation_audit`, OS-per-major template machinery (#643, V16 = 24.04/py3.12).
- **Tools lacking:** V16 switch leg; V16-specific fixups discovered by running.
- **Proof → `migration_proofs/S3.log`:** lands 16.x; `customisation_audit`
  V13-vs-V16 = **same-or-better**; V16-leg fixups verified.

### S4 — Full unattended clean run + merge
- **Objective:** prove the whole chain runs **unattended from a clean V13 substrate
  to V16 in one pass** (the "fully automated" exit), then merge the branch.
- **Deliverable:** top-level chain macro (composes S1+S2+S3) + a captured clean
  end-to-end run + `esacp-qa` approval.
- **Tools available:** everything above.
- **Tools lacking:** the chain macro; final `esacp-qa` pass.
- **Proof → `migration_proofs/S4.log`:** single command, clean V13 → V16, exits 0;
  **both** end-products pass structural A/B same-or-better; `esacp-qa` approves merge.

---

## Post-migration mini-projects (join the main plan AFTER S4)

Operator directive (S2, 2026-06-10): two tenant-logic **redesigns** are part of
the **main plan**, sequenced **after all other migration issues are resolved**
(once V13→V15→V16 is proven for everything else). They are carried through the
migration **as functionality, not as their bad code** — never hacked mid-migration.

- **M1 — Commission redesign (kill one-column-per-product).** `Sales Partner
  Customer Item Commissions` stores one column per product; an end-user cannot add
  a product without a schema change. **Live trigger:** end-user requesting the
  **"Polvo de Roca"** variants. Redesign to an end-user-addable (row-per-product)
  model. Memory: `commission_carry_forward_priority`, `post_migration_mini_projects`.
  Execution home: Plan-B Phase 4 (LSKB#6/#14/#16) — sequencing now main-plan.
- **M2 — Returnable serial-number redesign.** Serial-number $0.01 valuation
  doubling-cascade → float overflow; full domain-model rewrite of the
  out→returned→consumed→out cycle. Memory: `returnable_valuation_cascade`.
  Execution home: Plan-B Phase 8 (LSKB#10) — sequencing now main-plan.

Both are **gated on the migration's same-or-better proof** (S1–S4). Do NOT start
either until that is demonstrated.

---

## Session log — proof-of-delivery ledger (append at each session end)

Format per entry: `<step-id> | <date> | deliverable | proof command | migration_proofs/<step-id>.log | <commit>`

- S0a | 2026-06-10 | migration_status probe + hosts_map lookup-drift fix + SessionStart wiring | `./tools/test_migration_status.py && ./tools/test_host_identity.py` | migration_proofs/S0a.log | d1686f7
- S0b-bench | 2026-06-10 | V13 prod-data baseline established on dev01 (not dev02=V16); delta_report_dev01.json (373 drifts) + guard test + `--write` persistence | `./tools/customisation_audit/test_baseline_dev01.py` | migration_proofs/S0b.log | 613f4bb
- S0b-triage | 2026-06-10 | operator sign-off of all 22 behavioural entries (2 high / 6 medium / 14 wont_test); catalogue operator_confirmed + business_relevance + triage_note; drift_evidence_index.md binds every drift to its docs | `python3 -c "import yaml; from tools.bespoke_root import BESPOKE_ROOT; … entries==22 and confirmed==22 and tbd==0"` (full cmd in log) | migration_proofs/S0b-triage.log | LSV:8bf3271
- S1 | 2026-06-10 | automated 10-stage V13→V14 (`upgrade_to_v14.py`); 5 pipeline fixes #688/#331/#689/#690/#691; legacy_error_fixes homed in LSV; V13→V14 structural A/B LOST=0 + 11 stock property-setter additions | `./tools/customisation_audit/test_s1_v14_zero_loss.py` | migration_proofs/S1.log | 2f24279
