# 2026-05-30 0949 — Session 87 minutes

## Stated objective

Investigate **#473** — the tenant Custom Report `ejm` (Sales Analytics
wrapper) reported as 500-erroring on V16 — to root cause, then decide
fix scope. Operator acknowledged the objective at session start.

Outcome: **#473 is not a defect.** Closed `not planned`.

## Class

**Substantive — V13→V16 defect disposition (no-defect close).** The
objective close is the substantive spine. Coupled to it: one
operator-directed reinforcement of an existing feedback memory (the
lesson learned *from* #473), and two tracker issues filed from the
follow-on reporting-tools discussion (#526, #527). Not a sidebar — no
MEMORY.md indexing change, no carry-forward operator-reminder
attrition. The memory edit is content reinforcement of one existing
file, tightly coupled to the objective, not a memory restructure.

## What happened

### Pre-flight

- sync_check: **48 pass / 9 warn / 0 fail** (long-standing WG hub peer
  drift + dormant dev03/target5 + Cytoscape-API-not-running + Chrome
  manual-verify; all non-blocking).
- Open ESACP issues at start: **72** (agenda predicted 71; +1 = #523
  filed between S86 post-close patch and S87 start — the
  Co-Authored-By model-string reconcile chore; not a surprise).
- LSKB: **12** (matches). ce_sri: **5** (the S86-flagged −1 delta
  confirmed settled).
- TRIVIAL_FIXES.md: 3 entries unchanged.

### #473 — root-caused as not-a-defect, closed not_planned

The issue was filed at S78 off a `curl … -F 'filters={}'` (bare /
incomplete-filter) reproduction, recording two 500s:

- `'NoneType'.startswith` — missing `doc_type` filter.
- `KeyError: 'value_quantity'` — missing the required Sales Analytics
  `value_quantity` (Value/Quantity) filter.

S79 had recorded "same 500 on V13" and demoted to
"always-broken-with-default-filters."

**Operator overrode the recorded reproduction with lived verification**:
ran `ejm` on dev02 V16 from the **report screen** with proper filters
and got **valid, correct numerical results** — same numbers as prior
runs — and confirmed the report is **abandoned**. Operator's verbatim:
"I just tested ejm in dev02. Same numerical results. I observe that
your back-door testing was defective in that case."

Root cause of the recorded errors: **incomplete-filter invocation via
the test harness**, not the report or the platform. `doc_type` and
`value_quantity` are required Sales Analytics filters the report screen
supplies but the bare `curl` omitted. The "same 500 on V13" was the
same incomplete-invocation, not evidence of brokenness.

This is the **inverse** of `feedback_v13_v16_verification_depth`
sub-rule #2: an API/back-door *failure* misclassified as a feature
defect. Owned without deflection.

**T5 pre-issue-close** (esacp-qa `a0cc910255f1ccc43`): **approve**,
hard_block true. Comment `issuecomment-4582755222` records the
operator-confirmed result + the incomplete-filter root cause. Closed
`not planned` at `2026-05-30T11:59:24Z` (no fix → not "completed").

### Memory reinforcement (operator-directed)

`feedback_v13_v16_verification_depth.md`: sub-rule #2 extended to name
the **inverse direction** (API *failure* ≠ user-visible defect; never
write up a curl/console error as a defect without reproducing it from
the screen), and #473 added as a founding example. Edit is in the
LogiSoluMemory sibling repo; committed referencing #473. MEMORY.md
indexing untouched (file already indexed).

### Follow-on reporting-tools discussion → two issues filed

Operator asked which FOSS reporting tool (`temp/ReportingTools.md`)
best fits ESACP, assuming users ask the AI to author reports, Python
preferred (no JRE), and whether MCP is relevant. Analysis:

- Metabase (doc's headline pick) is **JVM/Clojure** → fails no-JRE.
  Jaspersoft/BIRT (Java) + Seal (.NET) out. Redash (Python) is
  maintenance-mode. **Superset** is the Python survivor.
- Key reframe: ESACP **already runs Grafana** (Go, no JRE) with a
  **live MCP connector**, and already has a **MariaDB MCP** for ad-hoc
  queries. The doc evaluates 6 external tools in a vacuum and misses
  the two surfaces already wired.
- **#526 filed** — AI-selected reporting layer: selection-heuristic +
  Grafana-MCP / Superset-MCP / Sheets evaluation (the load-bearing
  deliverable is the AI's "which tool for this request" rule).
- **#527 filed** — Google Sheets MCP connector so the AI can author
  AND verify the family-facing sheets the tenant's nightly Python
  data-pump produces. Emphasis comment (`issuecomment-4582803352`):
  explore the existing tenant Sheets first — reproduce the full
  richness (multi-tab transform chains, formulas, charts), not
  SQL→Python→drab inert tables. No-real-names rule applied (tenant =
  `LogiSolu` alias in the public issue).

## Counts at session close

- **ESACP open**: 72 → **73** (closed #473; filed #526, #527; net +1).
- **LSKB open**: 12 → 12 (untouched).
- **Sibling trackers**: ce_sri 5 / ce_sri_svc 2 / LSV 2 / BaRe 2
  (unchanged).
- **dev02 state**: V16 unchanged — only the operator's read-only
  report run; no lab mutation. `pre-S83-r1-acceptance` snapshot
  persists on toshy.
- **dev01 state**: V13 lab unchanged.
- **Saconsole**: 4 GiB; live.
- **TRIVIAL_FIXES.md**: 3 entries unchanged.

## Decisions

- **#473 = not a defect** — abandoned example report runs correctly
  from the screen; recorded 500s were incomplete-filter test-harness
  artifacts. Closed `not_planned`. Dropping the record is optional
  tenant-side (LSKB) cleanup, not a platform fix.
- **Reporting is a multi-surface capability, not a single-tool pick** —
  AI chooses the right surface per user request; catalogued in #526.
- **Sheets connector framed as fidelity-evaluation, not value-dump** —
  #527 must reproduce the tenant reports' real richness.

## Carry-forward (new from S87)

- **#526 / #527 open** — reporting-layer evaluation + Sheets MCP
  connector; future sessions, not on the V13→V16 critical path.
- **`ce_sri` −1 delta** — confirmed settled this session; drop from
  carry.

## Unchanged carry-forward (continues from S86)

- **#521 open** — common/config.py decomposition (87/80); mechanical
  sidebar or 1:1:1 refactor.
- **Option-tree-presentation feedback memory** — still to be promoted
  at next introspection sidebar (do not bundle with substantive work).
- **Stage 7 force-rerun exemption convention** — promote to
  architectural doc if a second exemption case appears.
- ESACP #426 / #427 — pending operator pickup.
- `on_boarding` branch handoff — Junior owns; #505 stays open.
- LogiSoluMemory cross-repo cleanup (~28 refs).
- ESACP#401 + dev02 intermittents.
- LSKB#11 / #16 / #18 / #21 — Phase 2/3 follow-on.
- LSKB#24 / LSKB#31.
- ESACP#387 / #394 / #395 / #396 / #397 — pre-S48 carry.
- TRIVIAL_FIXES.md monitors (3): `sync_check.sh:2 Mighty` (S58);
  `tools/secrets.py +x` (S47); LSMem T3-miss pattern (S33).
- S71 / S81 minutes backfill decisions.
- MariaDB-10.6 default PS=OFF (S55 carry).
- Tablet WG sidebar (#383).
- Pages site tenant-detail scrub gate.
- Stage-6-equivalent M&V check every ~50 substantive closes.
- Sub-rule #6 (operator walkthrough on systematic audits ≥2 findings).
- Frame-shift discipline (platform vs tenant M&V).
- Qualys regression-check as standard nginx-change acceptance.
- `applyV16PostMigrateFixups` primitive — canonical V13→V16 fixup entry.

## Diff-based introspection-sidebar trigger

**NEGATIVE.** No MEMORY.md indexing change; no operator-reminder
attrition (the `ce_sri` delta drop is a resolved-fact, not a reminder
aged out of the agenda). The one memory edit is content reinforcement
to an existing feedback file, coupled to the #473 objective. Class =
substantive.

## SESSION END audit (4 prongs)

1. **Forward-tense** — no orphaned "I'll"/"will" promises. #473 closed;
   #526/#527 filed with full bodies; memory edit made (commit pending
   in close batch).
2. **GH issue references** — #473 closed `not_planned` (no fix → no
   `fixes` keyword, correct). #526/#527 filed. No ambiguous states.
3. **PRs opened** — none this session (no code change; doc/issue work
   only).
4. **Unresolved operator doubts** — none lingering. Sheets-connector
   fidelity question homed in #527.
