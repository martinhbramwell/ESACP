# 2026-05-24 0707 — Session 78 minutes

## Session number

78 (S78). Second V16 walkthrough session — first verification phase.

## Objective — stated

Per S77 next-agenda, V16-walkthrough candidate A: Agenda 00
**verification** on LSKB (continuation of S77 enumeration). Operator-
confirmed scope: **verify-only** (fill `observed (V16)` + `verdict`
columns for all 53 active rows; LSV-spec column deferred to a backfill
issue per the agenda's own per-row Playwright-codegen-strict spec
being prohibitively expensive to fold into one session at ~46
captures).

## Objective — actual outcome

Achieved. LSKB#27 filed → branch cut → 53 rows verdicted via
Claude-in-Chrome on dev02 V16 → 3 defects promoted live during the
walk (LSKB#28, ESACP#472, ESACP#473) → 1 enumeration metadata defect
corrected inline (Company-envases_llenos/sucios `Link → Account`, not
`Link → Envases Llenos/Sucios`) → ESACP#456 root-cause hint commented
on the existing issue → committed → pushed → PR#29 squash-merged →
LSKB#27 auto-closed → LSV-spec backfill follow-up filed as LSKB#30.

## Pre-flight

- Controller: this machine. Branch: `main`, clean.
- `bash platforms/kvm/sync_check.sh` → 45 / 10 warn / 2 fail.
  Failures = dev01 unreachable (carve-out) + dev02 HTTP 404 (#456 —
  expected). No action.
- Open ESACP issues at session-start: **63** (matches S77 agenda).
- Open LSKB issues at session-start: **9** — agenda forecast 8; +1
  delta attributable to agenda undercount (LSKB#24 was open at S77
  close timestamp, not a new arrival). Not a real signal.
- dev02 versions confirmed: frappe 16.18.3 / erpnext 16.19.1 (V16).
- Playwright codegen present (`npx playwright codegen --help`
  responded with full options list).
- Claude-in-Chrome MCP tools loaded via ToolSearch (tabs_context,
  navigate, find, get_page_text, javascript_tool,
  read_console_messages, browser_batch, select_browser).
- LSKB residue from S77: working tree was still on
  `feat/25-agenda00-enumeration` (merged) and `main` was behind by 2
  commits — cleared via `git checkout main && git pull --ff-only`
  pre-branch.
- dev02 snapshotted `pre-S78-agenda00-verification` on toshy via
  `tools/pipeline/orchestration/snapshot_ops.create_snapshot()` with
  `hypervisor='toshy'` — via the pipeline primitive again (ESACP#440
  still open).

## What happened

1. **Operator choice confirmed**: Candidate A (Agenda 00 verification)
   over Candidate B (Agenda 05 naming-series). Confirmed after concise
   elaboration of both options.
2. **Scope decision** = **verify-only** (option 2 of 3 in the LSV-
   strictness question). Recommendation accepted: prove the
   verification mechanic on the easy material before committing to ~46
   Playwright codegen captures.
3. **LSKB#27 filed** as the verification tracking issue with explicit
   scope + acceptance criteria + cross-refs (LSKB#25 enumeration,
   ESACP#463 omnibus park, ESACP#456 home_page).
4. **Branch cut**: `feat/27-agenda00-verification` off LSKB `main`.
5. **Chrome browser selection**: two browsers connected (Linux +
   Windows). Asked operator; Linux selected. Windows is the
   on_boarding/Junior browser, off-limits.
6. **Operator-typed Administrator login** on dev02 desk (per safety
   policy — Claude does not type passwords into web forms even for
   lab admin). Confirmed logged in as Administrator at
   `https://dev02.iridium.blue/desk`.
7. **Walkthrough by category, all 11 categories**, using
   `frappe.db.get_value` + `frappe.model.with_doctype` + `frappe.get_meta`
   round-trips in the desk JS console for fast DB + meta confirmation,
   with selective HTTP fetch + render-test for Print Formats / Web
   Pages / Web Forms / Reports.
8. **Three defects promoted live**:
   - **LSKB#28** — `FdI: Cotización` (html=`<hr>` 4 chars) +
     `PF: O. de V. 2` (html=NULL) bespoke Print Formats have empty/
     null Jinja bodies. Single issue covering both — shared likely
     cause (loss during migration chain or always-empty).
   - **ESACP#472** — `/tasks` Web Form bare route returns 404 on V16.
     Other 5 Web Forms auto-redirect bare-route → `/list` or `/new`
     correctly; `/tasks/new` + `/tasks/list` also work. Likely
     Task DocType website-routing intercepts the bare route on V16.
   - **ESACP#473** — `ejm` Custom Report (~2.4kB column JSON,
     wraps erpnext `Sales Analytics` script report) HTTP 500s in two
     ways: bare run hits `'NoneType'.startswith` from
     sales_analytics.py:65 (missing `doc_type` filter); with filters
     supplied hits `KeyError: 'value_quantity'` — V16 script-report
     filter contract has tightened beyond what the Custom Report
     wrapper's stored JSON supplies.
9. **One enumeration metadata correction inline**: Company-
   envases_llenos / envases_sucios fieldtype column in the agenda
   incorrectly read `Link → Envases Llenos/Sucios`; actual `options`
   on V16 is `Link → Account`. Corrected in the same commit as the
   verdict-fill (1-cell housekeeping fix on rows already being
   edited).
10. **ESACP#456 root-cause hint** captured during Web Page category
    verification: `Website Settings.home_page="home"` but no
    `Web Page` row has `route="home"` on dev02 V16. Posted as
    [issuecomment-4528223097](https://github.com/martinhbramwell/ESACP/issues/456#issuecomment-4528223097)
    on #456 — three potential fixes enumerated, decision deferred to
    #456's own session.
11. **One incidental console error** (`Error connecting to socket.io:
    Invalid origin`) observed on every desk page load. Not per-row;
    out of scope for #27 — flagged for possible inclusion in #463
    omnibus or a dedicated socket.io-origin issue at session close
    (not filed this session — non-blocking, already-known-class).
12. **esacp-qa T1+T3 combined** on LSKB commit `85cd865`:
    `approve-with-conditions` / `hard_block:false`. One cosmetic
    condition (commit message claimed "47 × works" but file contains
    46 with 1 moot) — applied: `46 x works` before commit.
13. **Commit `85cd865`** on LSKB (GPG-signed, Co-Authored-By trailer,
    `fixes #27` in body).
14. **Push + PR#29 opened** on LSKB.
15. **esacp-qa T2 advisory carve-out** on PR#29 per §2.2 conditions
    all met: single-commit branch + prior approved T1+T3 + no rebase/
    cherry-pick/amend + squash merge. Verdict: `approve` / no
    conditions.
16. **PR#29 squash-merged via commit `c292e47`**,
    `mergedAt: 2026-05-24T11:06:44Z`.
17. **LSKB#27 auto-closed**, `closedAt: 2026-05-24T11:06:45Z`.
18. **LSKB residue cleared post-merge**: `git checkout main && git
    pull --ff-only` — clean main tip at `c292e47`, branch
    `feat/27-agenda00-verification` retained per `feedback_keep_merged_branches.md`.
19. **LSV-spec backfill follow-up filed** as **LSKB#30** — explicit
    deferred-from-S78 issue with scope (~46 `works` rows), out-of-
    scope (broken/moot/n/a rows), approach (operator-decided codegen
    style), acceptance.

## Decisions

- **Scope = verify-only** (operator chose option 2 of 3 in the LSV-
  strictness question; lowest risk for first verification walkthrough,
  defers the expensive ~46 codegen captures behind a follow-up
  issue).
- **One LSKB issue covers both empty PFs** (LSKB#28) rather than two
  separate issues — shared likely cause (migration-chain data loss
  or always-empty) and grouping is the high-information framing for
  a single fix sprint.
- **/tasks 404 → ESACP, not LSKB** — Web Form bare-route routing is
  V16 platform behavior, not tenant business logic; defect routes to
  ESACP per bucket framing.
- **`ejm` report 500 → ESACP** — same reasoning: V16 erpnext
  filter-contract tightening, not tenant business logic. The fact
  that `ejm` itself is a tenant-saved Custom Report doesn't change
  the failure surface, which is `erpnext/selling/report/sales_analytics/sales_analytics.py`.
- **IRS 1099 Form → `moot`** — US tax artifact, never used by
  Ecuadorian tenant. No defect filed despite render error; verdict
  carries explanation inline per acceptance criterion.
- **Enumeration metadata correction inline, not separate fix** — one
  cell change on rows already being verdicted; below TRIVIAL_FIXES
  threshold; below filing threshold.
- **ESACP#456 hint posted as a comment, not a new issue** — same
  root-cause class already tracked by #456; new comment adds
  diagnostic value without creating duplicate tracking.
- **Verify-only acceptance defined as verdict + observed columns,
  NOT LSV-spec column** — explicit deviation from agenda README's
  strict spec, tracked via LSKB#30 as the deferred work; close-batch
  qa-log row will note this so future sessions can read the
  precedent.

## Outputs

| Artifact | Repo | Status |
|---|---|---|
| Issue #27 (Agenda 00 verification) | LSKB | closed via merge |
| Issue #28 (2 bespoke PFs empty/null Jinja body) | LSKB | open |
| Issue #30 (LSV-spec backfill follow-up) | LSKB | open |
| Issue #472 (/tasks Web Form bare-route 404) | ESACP | open |
| Issue #473 (`ejm` Custom Report 500) | ESACP | open |
| Comment on #456 (home_page root-cause hint) | ESACP | posted |
| Branch `feat/27-agenda00-verification` | LSKB | merged, persists on origin |
| Commit `85cd865` (1 file, +62 / −53) | LSKB | merged via squash to `c292e47` |
| PR #29 / squash-commit `c292e47` | LSKB | merged 2026-05-24T11:06:44Z |
| Snapshot `pre-S78-agenda00-verification` on toshy/dev02 | (libvirt) | retained alongside prior 9 snapshots |

## QA verdicts

- **T1+T3 combined on LSKB commit `85cd865`** (per v2.1 §2.1):
  `approve-with-conditions` / `hard_block:false`. One cosmetic
  condition (commit message "47 × works" → "46 × works") discharged
  pre-commit.
- **T2 on PR#29 → LSKB main** (squash): `approve` under v2.1 §2.2
  carve-out. All three conditions independently verified by QA agent:
  prior T1+T3 approve covers the only commit; no commits added since;
  no rebase/cherry-pick/amend.
- **T5 (pre-issue-close) on LSKB#27**: auto via `fixes #27` in commit
  body; not separately invoked.
- **Session-close T1+T3 on ESACP main** (this commit covering S78
  minutes + S79 next-agenda + qa-log S78 close-batch row): _to be
  invoked next._

## Carry-forward (new from S78)

- **Agenda 00 LSV-spec backfill pending** (LSKB#30) — ~46 `works`
  rows need Playwright `.spec.ts` files in LogiSoluValidations to
  satisfy the README's strict acceptance spec. Operator-decided
  whether to do this as a dedicated session or fold into the next
  walkthrough's authoring flow.
- **3 V16-reassessment defects open** awaiting operator triage:
  - LSKB#28 (bespoke PFs empty/null) — fix likely requires
    migration-chain investigation to know whether to restore from
    PRODUCTION_20260404 or accept as always-empty + drop.
  - ESACP#472 (/tasks 404) — needs comparison with V13 site to confirm
    regression class.
  - ESACP#473 (`ejm` report 500) — operator-decision: re-author with
    V16 filter shape, or drop the report.
- **`socket.io: Invalid origin`** console error on every desk page
  load — not per-row defect, not filed this session (already-known-
  class, non-blocking). Watch for a third occurrence or operator-
  visible symptom before filing.
- **Agenda 00 verification phase COMPLETE** — supersedes the S77
  carry-forward "Agenda 00 verification pending" item. The remaining
  agendas (05, 06, 01, 04, 03, 02, 07) are the next units in the
  walkthrough order.
- **−1 delta hypothesis from S77** — closed out by virtue of S78
  verification: the 7-of-11 "missing" items per the enumeration delta
  table all turned out to be either present (sampling resolved them)
  or accepted as not-on-this-tenant (POS Invoice / RfQ Web Forms,
  IRS 1099 Form moot). No item represented a V16 regression; all
  were stale-baseline.

## Carry-forward (unchanged from S77)

- ESACP#440 `snapShotVM` CLI hypervisor-arg bug — re-encountered AGAIN
  this session at pre-flight (3rd consecutive walkthrough session;
  promote to primary candidate at next session per S77's carry rule).
- S71 minutes backfill decision still pending.
- ESACP#426 / #427 — pending operator pickup.
- on_boarding branch handoff — Junior owns.
- LogiSoluMemory cross-repo cleanup (~28 stale `docs/` refs).
- ESACP#401 (saconsole) + dev02 intermittent pings.
- LSKB#11 / #16 / #18 / #21 — Phase 2/3 follow-on.
- LSKB#24 (Agenda 04 SPC-test-pass) — still open.
- ESACP#387 / #394 / #395 / #396 / #397 — pre-S48 carry.
- `sync_check.sh:2 Mighty` (S58 TRIVIAL_FIXES).
- `tools/secrets.py +x` (S47 TRIVIAL_FIXES).
- T3-miss pattern (S58) monitor.
- MariaDB-10.6 default PS=OFF (S55 carry).
- LSMem Trigger-3 skip pattern (2 events monitor-only).
- Tablet WG sidebar (#383).
- Pages site is live — tenant-detail scrub gate.
- `session_focus.txt` / `session_buckets.txt` controller-root placement.
- `project_wip_consolidation_plan.md` `returnable` → `BtlMng` rename note.
- Stage-6-equivalent M&V check every ~50 substantive closes.

## Memory changes

None. No new feedback pattern emerged. The session was a clean
application of existing process: 1:1:1 discipline on LSKB,
plain-language approval requests honored, dead-end options pruned
(LSV-strictness question presented as 3-option prose with explicit
recommendation), defects filed at moment of discovery per bug
workflow, QA verdicts invoked at every trigger, PR merged before
session close per `feedback_pr_merge_before_session_close.md`. The
operator's S77-noted `feedback_plain_language_approval_requests.md`
and `feedback_prune_dead_end_options.md` continue to be honored
without re-prompt.

## Counts

- ESACP open issues: **63 → 65** (+2 from #472 + #473 filings; no
  ESACP closes).
- LSKB open issues: **9 → 11** (+2 net: #27 filed + closed in same
  session = 0; #28 filed = +1; #30 filed = +1).
- Sibling-tracker counts unchanged: ce_sri 6 / ce_sri_svc 2 /
  LogiSoluValidations 2 / BaRe 2.
- dev02 state: V16 substrate unchanged (read-only DB queries +
  read-only HTTP GETs only; no writes, no submits, no edits).
- Snapshots on dev02: 9 prior + `pre-S78-agenda00-verification` = 10
  retained.
- TRIVIAL_FIXES.md: unchanged (3 entries).

## Files committed (ESACP this session)

This commit only: S78 minutes + S79 next-agenda + qa-log S78
close-batch row.

## Session classification

**1:1:1 discipline on cross-repo (LSKB) substantive work** — one
issue (LSKB#27), one branch (`feat/27-agenda00-verification`), one
session, one PR. Substantive because verdict-filling on 53 rows
produced material V16-substrate findings (3 defects across 2 repos +
1 root-cause hint on existing issue + 1 follow-up issue filed).

Not housekeeping-bundle (substantive verification output, not doc
scrub). Not introspection-sidebar (no MEMORY.md edits; no
carry-forward operator-reminder attrition — additive only). Not
umbrella-branch (single discrete deliverable, no sub-branches).

Diff-based introspection-sidebar trigger evaluated: ESACP MEMORY.md
untouched, S79 next-agenda carries forward S78's operator-reminders
unchanged with additive new entries (3 new defects + LSV backfill
pending) without attrition of older items; trigger NEGATIVE.
