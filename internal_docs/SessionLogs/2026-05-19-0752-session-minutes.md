# 2026-05-19 0752 — Session 56 minutes

## Objective

Resolve ce_sri#10 (`forma_de_pago_preferida` Custom Field fixture-import collision) so `bench migrate` on dev02 clears the fixtures phase, unblocking LSKB#15. Recommended sub-path A1 (idempotent fixture semantics) per S56 agenda; fall back to A2 (substrate-apply pre-clear) if A1 surfaced structural issues.

## Outcome — objective abandoned; session pivoted to filing ESACP#400 (buffer-overflow audit)

Investigation reproduced a memory-handling failure mode the operator named **buffer overflow**: ce_sri#10's confident-sounding diagnostic body was accepted as authoritative without first grep-ing memory + recent minutes for the distinctive keywords (`forma_de_pago_preferida`, `tabDocField`, `tabCustom Field`). A single `grep -r forma_de_pago_preferida memory/` would have surfaced [`project_cesri_modules_fixture_bugs.md`](https://github.com/martinhbramwell/LogiSoluMemory/blob/main/project_cesri_modules_fixture_bugs.md) "Bug 3" (filed 2026-04-04, GH #96) — **same fieldname, same collision class, same root-cause analysis, and the institutional DELETE statement already shipped in BaRe `45b8775` + generic `g2_clear_fixture_custom_fields.py`**. The empirical re-derivation that followed was wasted work.

The operator escalated this from a session-level setback into a multi-session audit (ESACP#400) reassessing whether Plan-B execution has drifted from Plan-B / M&V planning more broadly, on the hypothesis that the same buffer-overflow pattern has produced unidentified drift across the S11→S56 window.

## Steps executed

| # | Step | Outcome |
|---|---|---|
| 1 | Standard session-start: identify platform (Mighty), `sync_check.sh` (46/9/2 — within agenda-expected window, dev01 disposable failures), verify open-issue counts (ESACP 41 / LSKB 8 / ce_sri 6 / LogiSoluValidations 2 — all match S56 agenda), trivial-fixes buffer scan (2 entries, monitor-only) | ✓ |
| 2 | Read ce_sri#10 body — accepted its "CustomField vs CustomField collision" framing as authoritative; enumerated 3 fix paths as starting plan | **✗ buffer-overflow trigger** — should have grep-ed memory first |
| 3 | Bisect-first investigation (per `feedback_bisect_before_hypothesizing.md`): query dev02 mariadb for the live row; read Frappe v13.58.22 `import_file.py:import_doc` from PRODUCTION_20260404 | ✓ — but should have come *after* memory grep, not as substitute |
| 4 | Surprise: `SELECT COUNT(*) FROM tabCustom Field WHERE fieldname='forma_de_pago_preferida'` returned **0**. The body's "production data already has the row in tabCustom Field" premise is empirically false | ✓ |
| 5 | Schema check: column exists on `tabCustomer` (1 col); `tabDocField` parent='Customer' has **1 row** (autoname `4c1b458226`, idx 45). The drift carrier is in DocField | ✓ |
| 6 | Verify the in_place_core_edit: `grep forma_de_pago_preferida` in `PRODUCTION_20260404/apps/erpnext/.../customer.json` → **2 occurrences** (fields array + field_order) | ✓ — drift confirmed |
| 7 | Quantify production-data exposure: `tabCustomer` has 1,808 rows; **100% non-null** for forma_de_pago_preferida; 1,378 use the default `Transferencia bancaria [20]`; **~430 carry non-default values** across 4 Mode-of-Payment options. Any conversion sequencing must preserve the column through `frappe.db.updatedb(dt)` (called from `CustomField.on_update`) | ✓ |
| 8 | Operator challenge: "I thought you had analyzed all of these repercussions weeks ago." | **Pivot moment** |
| 9 | Memory grep (the step that should have been step 0): `grep -lr "in_place_core_edit\|DocField.*CustomField" memory/` → 10 hits, including `project_cesri_modules_fixture_bugs.md` ("Bug 3", filed 2026-04-04 as GH #96) | ✓ — confirmed: every conclusion the investigation re-derived was already in memory, **with the institutional fix** |
| 10 | Operator framed the pattern as **buffer overflow** and proposed the 6-stage audit procedure with mandatory memory-grep gate per stage | ✓ — assistant confirmed understanding |
| 11 | File ESACP#400 — multi-session audit tracker ([link](https://github.com/martinhbramwell/ESACP/issues/400)) | ✓ |
| 12 | Write durable memory: `project_buffer_overflow_audit_plan.md` (audit procedure) + `feedback_grep_memory_before_issue_body.md` (new operating rule); MEMORY.md index updated | ✓ |
| 13 | Post diagnostic-correction comment on ce_sri#10 ([comment](https://github.com/martinhbramwell/ce_sri/issues/10#issuecomment-4487476604)); post block-chain-revision comment on LSKB#15 ([comment](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15#issuecomment-4487477932)) | ✓ |
| 14 | Write S56 minutes + S57 agenda; QA T1; commit; QA T3; push | (in progress) |

## Diagnostic findings (recorded as audit input, not session deliverable)

### Where the data IS

Table `tabDocField`, row name `4c1b458226`, parent `Customer`, fieldname `forma_de_pago_preferida`, idx 45. Loaded by `bench restore` from production's SQL dump; re-imported every `bench migrate` because customer.json is the source-of-truth for that DocType definition.

### Where the data SHOULD live (per ce_sri design)

Table `tabCustom Field`, row name `Customer-forma_de_pago_preferida` (per `CustomField.autoname` → `dt + "-" + fieldname`). Currently 0 rows on dev02.

### The validator that throws

`PRODUCTION_20260404/apps/frappe/frappe/custom/doctype/custom_field/custom_field.py:38-46` — `before_insert` calls `frappe.get_meta(dt, cached=False).get("fields")`, which is the **union of DocField + CustomField**. Drift row in DocField → fieldname appears already-taken → throw.

### The in-place core edit

`PRODUCTION_20260404/apps/erpnext/erpnext/selling/doctype/customer/customer.json` `fields` array + `field_order` — 2 occurrences of `forma_de_pago_preferida`. Read-only snapshot, but bench restore reproduces this state on every dev rebuild from production SQL dumps.

### Production-data column

`tabCustomer.forma_de_pago_preferida` — 1,808 rows, 100% populated. Distribution: 1,378 default / 391 Efectivo [01] / 18 Cheque [20] / 13 Cruce de cuentas [01] / 8 Depósito bancario [20]. ~430 non-default values are tenant-specific operational data that must not be lost across the drift→idiomatic conversion.

### Existing institutional fix

`memory/project_cesri_modules_fixture_bugs.md` "Bug 3" (GH #96, 2026-04-04):

```sql
DELETE FROM tabDocField WHERE parent='Customer' AND fieldname='forma_de_pago_preferida';
```

Shipped in BaRe `45b8775` (pre-migrate step in `handleRestore.sh`) and generalized in `g2_clear_fixture_custom_fields.py`. Verified working 2026-04-04. The real question (deferred to ESACP#400 audit) is **why this step did not run in LSKB#15's Plan-C substrate-apply on dev02 in S55**.

## GitHub issue activity

| Issue | Action | Mechanism |
|---|---|---|
| [ESACP#400](https://github.com/martinhbramwell/ESACP/issues/400) | **filed** — audit-tracking issue | New |
| [ce_sri#10](https://github.com/martinhbramwell/ce_sri/issues/10) | diagnostic-correction comment + stays open pending audit | Comment, not close |
| [LSKB#15](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15) | block-chain-revision comment + stays paused pending audit | Comment, not close |

## Pointer-comments posted

- ce_sri#10 — [Diagnostic correction (Session 56, ESACP#400)](https://github.com/martinhbramwell/ce_sri/issues/10#issuecomment-4487476604)
- LSKB#15 — [S56 status update — block chain re-framed; pending ESACP#400 audit](https://github.com/martinhbramwell/LogiSoluKnowBase/issues/15#issuecomment-4487477932)

## Memory files written

- `project_buffer_overflow_audit_plan.md` — audit procedure + scope window + report location + memory-grep gate
- `feedback_grep_memory_before_issue_body.md` — the rule extracted from this session's failure
- `MEMORY.md` — index updated with both pointers

## PR opened + merged

None. No code shipped this session; the work pivoted entirely to filing and recording the audit.

## QA verdicts

(filled in by post-write QA gates — see commit log)

## Trivial Fixes buffer

Unchanged (2 entries, both monitor-only):
1. LogiSoluMemory Trigger-3 skip pattern (S33 origin)
2. `tools/secrets.py` lost `+x` bit (S47 origin)

## Carry-forward operator-reminders (S57)

- **ESACP#400 (NEW S56)** — multi-session buffer-overflow audit. S58 = Step 1 (overall plan review + finalize stage list).
- **ce_sri#10** — diagnosis corrected, stays open pending audit conclusion; no longer "fix ce_sri fixture"; now "verify why BaRe `45b8775` + g2 step didn't run in Plan-C substrate-apply".
- **LSKB#15** — substrate-apply paused; block chain revised to flow through ESACP#400.
- **LSKB#16** — downstream of LSKB#15.
- All other carry-forwards from S55 agenda persist unchanged.

## State carried to S57

- ESACP open: 42 (S56: +#400 audit-tracker; +1 net).
- LSKB open: 8 (unchanged).
- ce_sri open: 6 (unchanged — #10 stays open).
- LogiSoluValidations open: 2 (unchanged).
- Branch: `main` (after S56 close-out commit lands).
- dev02 substrate state: unchanged from S55 close.
- Build evidence on dev02 (`/tmp/lskb15-S55-migrate*.log`): retained.
- **`internal_docs/qa-contract.md`**: v2.1 (unchanged).
- **`TRIVIAL_FIXES.md`**: 2 entries (unchanged).
- Cross-repo `fixes` tally: 18 (unchanged — no closes this session).

## Lessons (for the audit's record)

1. **Buffer overflow is a real session-level failure mode**, not a one-off. Confident-sounding issue-body diagnoses bypass the memory-grep step that would catch them. Operating rule landed: `feedback_grep_memory_before_issue_body.md`.
2. **Session-start protocol gap**: `sync_check.sh` does not (and probably should not) grep memory for the upcoming session's keywords — but the session-start procedure should explicitly include a memory grep against the agenda's named blockers. Candidate Stage 3 (memory hit-rate) of ESACP#400 will quantify how often this gap has cost work.
3. **Re-derivation is a tell**: when an investigation arrives at conclusions that read like "obvious in hindsight", the most likely explanation is that memory already records them and went unconsulted. That recognition should trigger an immediate `grep -r` against memory before continuing.
