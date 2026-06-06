# 2026-06-04 1123 — Session 103 minutes

## Objective (operator-pinned)

**#456** — V13→V16 website-root 404. Reproduce-and-compare first, then decide fix-path
and bucket. Outcome: **not a fix session** — the filed defect was already resolved; the
session instead **established a triage criterion** and **re-classified #456 as deferred**.

## Class

Substantive reasoning, but **no code / pipeline / config change**. Output is one memory
file (sister repo) + GitHub issue grooming (re-scope, label, comments). No ESACP-repo
commit, no PR, no issue close. Not a 1:1:1 code session; not an introspection-sidebar
(MEMORY.md got one *additive* index line, not restructuring — esacp-qa confirmed this does
not cross the diff-based sidebar trigger).

## What happened

### Reproduce-and-compare (#456)
- `curl -sI https://dev02.iridium.blue/` → **HTTP 200** (`x-page-name: home`, 10,682 B).
  The filed 404 is **fixed** by R1 (`r1_recreate_web_page_home.py`, #486).
- Compared dev02's rendered home against the **authoritative production DB dump**
  (`PRODUCTION_20260404` / `20260502`). Findings:
  - dev02's hero (`company` / `tag_line` / `description`) is
    **byte-faithful to production's `Homepage` singleton**. The "…sitio web de ejemplo
    generado automáticamente por ERPNext" text is **real production content** (tenant never
    customized ERPNext's seed copy) — **not** an R1 placeholder.
  - V13's `/` was ~103,520 B (rich) vs dev02's 10,682 B. That richness came from erpnext
    `templates/pages/home.{py,html,css}` + the `Homepage` portal DocType — **all
    upstream-deleted in V14/V15** (confirmed ABSENT on dev02). **No salvage can reproduce
    V13's look** — a faithful homepage is a *new V16 build*, not a data recovery.
  - Only surviving tenant content beyond the hero: one custom "About" `Homepage Section`
    (→ 2 links to `/terms-of-use` + `/privacy-policy`, both already HTTP 200 standalone).
    R1 reproduces hero only.

### The S88 reconciliation
Operator had reopened #456 at S88 ("not solved"). The bare-hero R1 page is the exact state
that was rejected. Surfaced this before any close — closing would have repeated the S88
mistake. Drove the session to the *right axis*: the homepage is low user-importance but must
still migrate ("when, not if").

### Triage criterion adopted (operator, S103)
Two-tier prioritization of the V16 cutover, with the cut decided by **evidence, not
judgment**:
- **Tier A — business-critical, blocks cutover.**
- **Tier B — owed but deferred** until all Tier-A proven good (`defer:post-business`).

**Criterion:** *if a migration detail can be shown connected with **significant recent DB
activity** → Tier A; otherwise the operator classifies it* (fallback is load-bearing —
silence routes to the operator, never to a guess). Operationalized: trace detail → backing
table(s) → `COUNT(*)` + `MAX(modified/creation)` within a recency window, measured against
the **backup snapshot date** (not live).

### Actions taken
- **Memory**: `project_v16_migration_triage_criterion.md` + MEMORY.md index line.
  Committed GPG-signed `fde6e07` (LogiSoluMemory), pushed `1076dc9..fde6e07`.
  esacp-qa pre-commit verdict = **approve** (no real names; links resolve; criterion
  faithful).
- **#456 re-scoped** (NOT closed): title → `chore(v16-upgrade): faithful V16 homepage
  rebuild (Tier B, deferred post-business) — R1 interim home→200`; added
  `defer:post-business`; kept `umbrella:480`; posted interim-state comment
  (`#issuecomment-4622532408`).
- **#480 umbrella**: criterion documented as the adopted catalog-triage method
  (`#issuecomment-4622535330`).
- Created repo label `defer:post-business`.

## End state
- **ESACP open: 78** (Senior net **0** — #456 re-scoped not closed, no issue opened/closed;
  +3 vs agenda's 75 is **Junior on_boarding churn**, not Senior).
- **LSKB open: 12** (unchanged).
- **#480 critical-path query** (`umbrella:480 --state open` minus `defer:post-business`) is
  now **EMPTY** — #456 was the last labeled child. Next concrete V16 critical-path item is
  the umbrella's own **fresh-substrate clean-run acceptance** (never run). The catalog sweep
  must therefore reach **beyond labeled children** into broader V16 concerns (#457, #463,
  #466, …).
- **dev02**: V16, homepage renders (R1 interim). Untouched at filesystem/VM level this
  session (read-only DB-dump inspection + curl only). `pre-S83-r1-acceptance` snapshot
  persists.
- **Working trees**: ESACP clean apart from Junior's untracked `on_boarding/onBoardingQRcode.png`
  (leave it). LogiSoluMemory clean (committed + pushed).
- **sync_check**: 48 pass / 9 warn (dormant VMs + Chrome manual note) / 0 fail.

## Decisions
- Homepage faithfulness is **Tier B** (deferred), proven by the DB-activity criterion
  (backing records stale since 2022), not by taste.
- The triage criterion is **ESACP bucket-1 methodology** (methodology-stays); execution of
  any tenant homepage *content* would be LSKB if/when picked up.
- Re-scope over close: #456 stays the single home for "homepage not yet faithful".

## Session-end audit
Clean — all forward-tense items durably homed (catalog-sweep in #480/#456 comments + memory;
commit `fde6e07` executed + pushed; #456/#480 findings posted on the issues themselves).
**One item for operator attention** (carried forward): the criterion's **thresholds are
proposed, not set** — recency window (proposed 90d) and the "significant" bar for
transactional doctypes vs config singletons. These are an **input the operator must set
before the catalog sweep**.
