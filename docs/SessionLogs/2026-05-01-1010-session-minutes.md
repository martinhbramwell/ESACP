# 2026-05-01 1010 — Session minutes

**Branch:** `feat/in-place-core-edits-classifier-317` (cut, merged via PR
#329, deleted from local; main now at `2e95cb0`).
**Objective (originally agreed):** Implement #317 Phase 4 — in-place
core-tree edits classifier — per the locked design (plan §7 +
`issuecomment-4356005616`).
**Objective extension (mid-session, operator-directed):** After PR #329
merged, run **Trial Flavour A**: cheap V13→V14 migration on dev01 to
validate the audit's predictions and surface unknowns. One-objective
discipline traded for two related ones in the same window.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` → 46 ✅ / 8 ⚠️ / 2 ❌ (both ❌
  expected: dev02 shut off per `feedback_one_vm_at_a_time.md`).
- Latest agenda: `2026-04-30-1641-next-agenda.md` — three options on
  offer; operator's four pre-session guardrails pinned implementation to
  Option A.
- Working tree clean; main at `4af4713`.

## Pre-implementation triage of operator guardrails

Operator listed four scope-discipline reminders before implementation
started. All registered:

1. address.json Drift count is `≥1` runtime-derived, not hand-counted.
2. Phase 2 row_data shim is deferred to #327, not #317's scope.
3. Audit prose is not load-bearing — runtime is. Don't pre-fix audit doc.
4. Untracked trees explicitly excluded — out-of-scope discoveries → new
   issue, not scope-creep.

## What ran — Implementation (PR #329)

Eleven SUT modules + seven colocated tests + 12 frozen fixtures captured
from `$BESPOKE_ROOT/PRODUCTION_20260404/apps/{frappe,erpnext}` at design
time. Wiring into `audit_config.AuditConfig.core_tree_root` + `runner`
DISCOVER_MODULES. Mechanical size cap at ≤50 lines added to
`tools/pre_commit_size_check.py` for each new SUT module.

### Design call (documented in PR #329 body)

The locked rule-5 noise filter (timestamp / `"states": []` / EOF newline)
was extended to a **JSON-semantic `has_new_business` check**:
- Permissions compared by `role`
- Fields compared by `fieldname`
- Top-level by key (excluding `permissions` / `fields`)
- Deletion-dominant diffs (>2× removed chars vs added) treat new
  fieldnames as v12→v13 reformat artifacts

This handles Frappe v12→v13 schema-default reformats — v13 adding
`"create": 1` to existing perms, `"unique": 1` schema defaults,
deletion-dominant resaves of v12-format files. Without this extension,
`party_type.json` and `sales_partner.json` (acceptance #3) would have
fallen to `human_review_core_edit` fallback.

### Acceptance criteria — all 9 green

| # | Result |
|---|---|
| 1 | `identify_bad_customisations.py --substrate dev01` → 31 in-place + 360 DB-side = 391 total |
| 2 | `user.json` → 2 fixture_equivalent_core_edit + fixture_json (HR Manager × 2) |
| 3 | `party_type.json`, `sales_partner.json` → 1 discardable each |
| 4 | `address.json` → 2 Property Setter Drifts (`delivery_route`, `barrio`) |
| 5 | `delete_doc.py`, `document.py`, `requirements.txt` → 1 human_review each |
| 6 | `erpnext/translations/es.csv` → 1 app_translations_csv |
| 7 | All new SUT modules ≤50 lines, mechanically enforced (TARGET_LIMITS) |
| 8 | 7 colocated tests, all passing |
| 9 | No source-tree mutation |

### PR / commit

- Commit `bfba5c2` (re-committed cleanly after a heredoc-quoting issue
  on the first attempt — `git reset --soft HEAD~1` + `git commit -F` from
  a file).
- PR `#329` opened with comprehensive body (architecture, design call,
  acceptance, test plan, Phase 2 hand-off note).
- Merged 2026-05-01T12:35:49Z (`2e95cb0`).
- `#317` auto-closed at 12:35:50Z.
- Validation comment posted to `#317` (`issuecomment-4359680990`) with
  trial-derived empirical numbers.

## Operator decision-rule registered

Mid-session, operator clarified the V14→V16 readiness rule:

> Is the artefact certain to pass unaltered all the way up the version
> migration ladder to V16? If yes, ignore it.

Applied to the 232 `db_only` drifts in the report:
- All ride through `bench migrate` intact (Custom DocPerm, Custom Field,
  Custom DocType, Translation, Print Format).
- Client/Server Script *rows* survive but *bodies* may not (separate
  audit, gated on successful trial — filed #330).
- No compelling reason for proactive attribution; the three usual
  justifications (parallel test envs, DR without data, sister business)
  all fail this operator's reality.

Saved as `feedback_db_resident_customisations_acceptable.md` and indexed
in `MEMORY.md` under Critical Rules.

## What ran — Trial Flavour A on dev01

| Step | Result |
|---|---|
| `virsh snapshot-create-as dev01 pre-trial-A` | ✅ |
| Tar 5+18 modified files from PRODUCTION_20260404, scp to dev01, extract into `frappe-bench/apps/{frappe,erpnext}` | ✅ — `git status` matched audit exactly |
| `virsh snapshot-create-as dev01 v13-plus-edits` | ✅ |
| `bench switch-to-branch version-14 frappe erpnext --upgrade` | ⚠️ frappe + erpnext switched cleanly (force-checkout silently wiped 23 in-place edits) — crashed mid-flow at bespoke-app `uv pip install` (gunicorn URL dep) |
| Workaround: `uv pip install --no-deps -e apps/<bespoke>` × 3 | ✅ |
| `bench migrate` | ✅ exit 0 — V14 patches all ran, including 46,300-row GL Entry → Payment Ledger Entry migration |
| Restart supervisor (workers/web), `bench build`, restart web again | ✅ HTTPS returns 200, login renders |

### Audit predictions vs reality

| Audit said | dev01 V14 reality |
|---|---|
| 23 in-place edits silently wiped by `git checkout -f` | ✅ 0 modified files post-checkout |
| `delivery_route` + `barrio` field defs lost | ✅ JSON has upstream v14 only |
| `tabAddress` columns survive (DB schema not dropped) | ✅ both present |
| **Production data orphaned** | ✅ **162 records have non-null `barrio` data, no field renders them** |
| HR Manager perms on User were JSON-only, no `tabCustom DocPerm` row | ✅ confirmed — 0 rows |
| DB-resident: Custom Field=56, Custom DocPerm=203, Translation=10, Custom DocType `Barrio`: survive | ✅ all present, counts unchanged |

Phase 4 audit confirmed dead-on accurate.

### New V14 cutover findings (filed)

- **#331 — Bespoke-app `uv pip install` crash on Frappe v14 gunicorn URL dep.**
  Root cause documented; workaround proven on dev01. Recommended fix:
  codify the workaround in Phase 5 `upgrade_to_v14.py` (Option A in the
  issue body). V14 cutover blocker.
- **`bench build` required manually post-upgrade.** Likely consequence of
  #331 crashing the upgrade flow before its own build step. Not filed
  separately — handled inside #331's fix scope.

### Issue trigger fired

- **#330** (Client/Server Script v14 API-compat audit) — was parked
  behind a successful-trial trigger; trigger has fired. Comment posted
  (`issuecomment-4359681048`). Issue eligible for active work whenever
  the operator picks it up.

## State at session close

- **main**: `2e95cb0` (PR #329 merged).
- **dev01**: now on V14 (`frappe 14.101.1` / `erpnext 14.92.14`),
  serving `https://dev01.iridium.blue` HTTP 200. Snapshots available for
  one-step revert: `Baseline`, `ERPNext v13 Restored Baseline`,
  `pre-trial-A`, `v13-plus-edits`.
- **Open issues filed today**: #330 (V14 script API-compat, gated /
  trigger now fired), #331 (gunicorn URL dep, blocker).
- **Open from before**: #317 closed; Phase 2 (#327) still design-locked
  not implemented; Phase 5 / Phase 6 not implemented.
- **Working tree**: clean.

## Memory updates

- New: `feedback_db_resident_customisations_acceptable.md`.
- Updated: `MEMORY.md` (added Critical Rules entry pointing at the new
  feedback file).

## Forward-tense audit (session-close)

Every "I'll X" in this session resolved either as (a) executed tool
call, (b) durable home (issue, comment, memory file), or (c) flagged
unresolved below. None deferred to "noted for next session."

## Unresolved at close (for operator attention)

1. **dev01 left on V14.** Operator question "keep there or revert?" not
   yet answered. Snapshots `pre-trial-A` and `v13-plus-edits` provide
   one-step revert paths. Note: leaving dev01 on V14 changes the
   substrate `identify_bad_customisations.py --substrate dev01` reports
   against — re-running the audit would show different DB content.
2. **3 `human_review_core_edit` items** unresolved as of close —
   `delete_doc.py`, `document.py`, `requirements.txt`. Each needs an
   operator decision (port to V14 / discard / replace) before production
   cutover. Not blocking the trial, but blocking production.
3. **Phase 2 (#327) implementation** still pending. Trial confirmed it
   is the load-bearing next step: without it, V14 cutover orphans the
   162 `barrio` records and loses the HR Manager User perms.
4. **`bench build` post-upgrade step** noted inside #331 rather than
   filed separately — that was a judgment call (consequence of the
   gunicorn dep crash, expected to be subsumed by #331's fix). Flag if
   you'd prefer a standalone issue.
