# 2026-05-05 1831 — Session 10 minutes (DB-resident customization discovery sweep)

## Stated objective at session start

Per `2026-05-05-0927-next-agenda.md`: execute the DB-resident customization
discovery sweep against dev02 and populate
`LogiSoluValidations/audit/customizations_catalogue.yml`. Revise README
Section N to reflect the inventory.

## How the session actually went

Three operator-driven scope shifts before code landed:

1. **Discovered ESACP already does most of the agenda's work.** While
   inspecting `tools/customisation_audit/` to understand what existed,
   surfaced 12 `discover_*` modules + `attribution.py` + a CLI dispatcher
   (`identify_bad_customisations.py`). The agenda's Phase 1 (DB enumeration
   of ~17 tables) and Phase 2 (three-frame cross-check via attribution
   YAML) were already implemented. Re-pivoted from "build a parallel
   sweep" to "reuse ESACP audit in place + write LogiSoluValidations
   gap-filler probes for the 6 tables ESACP doesn't cover + synthesise
   catalogue YAML."

2. **Operator clarified ESACP/LogiSoluValidations boundary.** Operator's
   first reaction was "move the audit code from ESACP to LogiSoluValidations,"
   then tempered to: "ESACP must retain a deep understanding of ERPNext.
   It does NOT need a detailed understanding of [the business's]
   customizations." Drew the line: mechanism stays in ESACP (generic
   ERPNext audit + lab infrastructure); content moves to LogiSoluValidations
   (`customisation_attribution.yml` + bespoke-apps list). Explicit "no
   upheaval at this point" — migration deferred to a future ESACP issue.

3. **README structure pivoted from full-checklist to prescriptive staffer
   subset.** Initial Spanish section had every section A–N with detailed
   "qué grabar" recipes. Operator corrected: the staffer already knows
   how to do these tasks; the list should be a **prescriptive subset** of
   workflows he routinely performs, with `<details>` collapsibles
   containing only **gotchas**, not how-to. Sections handled
   programmatically (translations, property setters, in-place core edits,
   permissions, print formats) come **off** the staffer list entirely.
   Status icons swapped from 🔴/🟡/🟢 ("Smarties") to ✅/⏳/❌ per
   operator's earlier preference (which I had misread).

## What landed

| Artefact | Location | Status |
|---|---|---|
| `audit/gap_filler_probe.py` | LogiSoluValidations sub-branch | Pushed |
| `audit/hooks_patches_scan.py` | LogiSoluValidations sub-branch | Pushed |
| `audit/customizations_catalogue.yml` (22 entries + 12 summary blocks) | LogiSoluValidations sub-branch | Pushed |
| `audit/_work/*.json` (3 working dumps) | LogiSoluValidations local only | Gitignored |
| README revision (Spanish staffer section + Section N cross-link registry) | LogiSoluValidations sub-branch | Pushed |
| [PR #1](https://github.com/martinhbramwell/LogiSoluValidations/pull/1) opened to `umbrella/playwright-regression-suite` | LogiSoluValidations | Awaiting operator review |
| Comment on [ESACP #312](https://github.com/martinhbramwell/ESACP/issues/312#issuecomment-4383641982) with catalogue link | ESACP | Posted |
| [ESACP #351](https://github.com/martinhbramwell/ESACP/issues/351) — audit-engine parameterisation | ESACP | Filed |

## Discovery probes — coverage map

ESACP's `tools/customisation_audit/` covers 11 of the agenda's 17 tables:
server_script, client_script, custom_doctype, custom_field, property_setter,
print_format, translation, workflow, custom_docperm, naming_series, plus
in_place_core_edit. Custom-attributed rows (e.g., 56 Custom Fields, 194
Property Setters, 7 Client Scripts) are suppressed in audit drift output —
they're already declared in `customisation_attribution.yml`.

The gap-filler probe covers 6 tables ESACP audit doesn't: Notification
(5; all stock-verified), Auto Email Report (0), Dashboard Chart (0), Web
Form (0), Scheduled Job Type (104; 1 bespoke / 103 stock), Role (67;
mostly stock). Plus Workflow State (3 stock convention), Workflow Action
Master (3 stock convention), and Report (1: `ejm` — likely test artefact).

The hooks/patches scan parses each bespoke app's `hooks.py` for
behavioural wiring + `patches.txt`. Findings: ce_sri's hooks.py declares
fixtures + install hooks only (all behavioural logic in DB Server
Scripts); returnable wires `Delivery Note.validate → startStockEntry`
plus a per-minute cron `returnableMoveFromMaterialTransfer`; route_planner's
hooks.py has no behavioural wiring (logic is all in DocType source).

## Catalogue contents (22 individual entries)

| Section | Entries | Examples |
|---|---|---|
| A (SRI flow) | 2 custom DocTypes | `Tasas de Retencion de IR/IVA` |
| A1 (commission) | 2 Server Scripts + 1 custom DocType | Sales Partner Commission Before Save / After Submit + `Sales Partner Customer Item Commissions` |
| B (Sales Order) | 1 Server Script | `Customer Balance` |
| E (Delivery Note) | 2 Server Scripts + 1 custom DocType + 2 hooks | DN Before Save / Before Submit + `Bought Returnable` + returnable's `startStockEntry` + every-minute cron |
| J (Translations) | 6 DB Translation rows | Owing, County, Tax Id, Make, Voucher, Gross YTD |
| M (Print Formats) | 3 ce_sri-attributed | `PF: O. de V. 2`, `FdI: Cotización`, `FdI: Factura de Venta ejemplo` |
| won't-test | 2 | `IRS 1099 Form` (US-only), Report `ejm` (likely test artefact) |

Plus 12 summary blocks for declared / deferred classes (custom_docperm
deferred to ESACP #330; naming_series informational; in_place_core_edit
classified by attribution YAML; etc.).

## Naming convention adopted in this session

`Logichem` (full client name) does not appear in any tracked file or
commit message. Production-data fields whose value would expose the
client identity (e.g., Frappe `module` strings) are stored as `bespoke`
placeholder per the catalogue's top-of-file `naming_conventions` block.
Apps named after their Frappe package path (`ce_sri`, `returnable`,
`route_planner`, `BaRe`) appear verbatim because those are public package
identifiers, not client names. `LogiSolu` is preserved as the
deliberately-ambiguous public name (the repo is `LogiSoluValidations`
and the staffer-section heading reads "Para el equipo de LogiSolu").

## QA verdicts during session

3 `esacp-qa` verdicts:

1. **Pre-commit on `feat(audit):`** — `approve-with-conditions`. Sole
   condition: `hooks_patches_scan.py` docstring claimed a fallback to
   `PRODUCTION_20260404` that wasn't implemented. Removed the false
   claim before commit landed.
2. **Pre-push attempt 1** — `approve-with-conditions` (hard-block).
   Caught two issues: `gap_filler_probe.py` size (148 lines, 101+ band)
   and Logichem leakage **in commit message bodies** (working tree had
   been scrubbed; commit messages had not). Operator override on the
   size; reset-and-recommit remediation on the messages — the original
   3 commits were collapsed into 2 with clean messages via
   `git reset --soft HEAD~3` + selective re-staging.
3. **Pre-push attempt 2** — `approve`. Push proceeded; PR #1 opened.

QA-log rows appended in same commit as these minutes.

## Honest gaps

- **Catalogue triage fields (`business_relevance`, `suite_section`,
  `operator_confirmed`) seeded with TBD/best-guess.** Operator triage
  via PR review or follow-up commits to the sub-branch fills these in.
  Per the agenda's step 4, this was operator work; not blocking the
  catalogue's landing.
- **Playwright scaffold not started.** No `package.json`,
  `playwright.config.ts`, or first spec yet. Session 11+ work.
- **No first spec recorded.** The staffer hasn't yet been onboarded
  with the family member; that's a real-world step before any
  recording lands.
- **ESACP audit migration to LogiSoluValidations not done.** Tracked
  as #351; multi-session umbrella effort, deliberately deferred per
  Session 10 scope decision.
- **Mac Mini + Chrome assumption unverified.** README states the
  staffer will use Chrome on a Mac Mini; this hasn't been confirmed
  with the staffer yet.

## Issues touched

- **ESACP #312** — comment posted with PR #1 link, catalogue scope
  summary, and Phase B completion claim.
- **ESACP #351** — new issue filed for audit-engine parameterisation.
- **LogiSoluValidations#1** — PR opened, awaiting review.

## Files at session-end

In ESACP doc-sweep commit (this commit on main):

- `docs/SessionLogs/2026-05-05-1831-session-minutes.md` — this file
- `docs/SessionLogs/2026-05-05-1831-next-agenda.md` — Session 11 agenda
- `docs/qa-log.md` — appended Session 10 verdicts

In LogiSoluValidations (PR #1 — `playwright-regression-suite/discovery-sweep`):

- `audit/customizations_catalogue.yml` — 545 lines (with `naming_conventions:` block)
- `audit/gap_filler_probe.py` — 148 lines, 10 functions
- `audit/hooks_patches_scan.py` — 103 lines
- `README.md` — 545 lines (Spanish staffer section + revised English Section N)
- `.gitignore` — adds `audit/_work/`

In LogiSoluValidations (local only, gitignored):

- `audit/_work/delta_report_dev02.json` — ESACP audit output
- `audit/_work/gap_filler_dev02.json` — gap-filler probe output
- `audit/_work/hooks_patches_dev02.json` — hooks/patches scan output
