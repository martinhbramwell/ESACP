# 2026-06-01 2110 — Session 92 minutes

## Stated objective

**Make the R2 `/tasks` 404 decision** on the #480 V13→V16 catalog — a call between
(a) app-level redirect, (b) nginx rewrite, (c) accept/won't-fix — then execute the chosen
option. Operator-set objective per the S92 agenda.

## Pre-flight

- `sync_check`: **49 pass / 8 warn / 0 fail** — all warnings expected (dormant dev03/target5
  across VM/WG/ERPNext checks, manual Chrome-tab verify).
- Open issues at start: ESACP **71** (agenda forecast 71), LSKB **12**. No drift.
- TRIVIAL_FIXES.md: 1 monitor-only entry (S33 LSMem T3 skip); nothing to clear.

## What happened

### Orientation — operator did not recognize the objective

Operator opened with "I have no idea what you are talking about." Dropped all jargon and
re-explained R2 in plain English: the test ERP site's "Tasks" form has three addresses —
bare `…/tasks` shows page-not-found, while `…/tasks/list` and `…/tasks/new` work; the bare
404 is a deliberate ERPNext V14+ convention change, not something we broke; the only task was
deciding what (if anything) to do about that one leftover checklist item.

### The decisive question — evidence of use

Operator asked the right gate question: **is there any evidence LogiSolu users ever accessed
the bare `/tasks` link?** Investigated rather than guessed:

- The bare route *would* have worked on production (older version still rendered it), so use
  was *possible*.
- Evidence would live in production web-server access logs. Checked the `PRODUCTION_20260404`
  snapshot — it holds app code + a DB backup but **no web-server access logs**.
- ERPNext's DB "Access Log" records document downloads/exports, **not** bare-page visits — so
  the backup can't answer it either.
- Conclusion relayed: **no evidence, and no feasible way to obtain it** (absence of evidence,
  not evidence of absence) — but the call is **fully reversible** (a Website Route Redirect is
  a ~20-min add if a real user ever complains). Strongest available signal is the operator's
  own knowledge of user habits.

### Live probe (grounding, not re-classification)

Probed dev02 before recommending: `/tasks` → 404, `/tasks/list` → 301, `/tasks/new` → 403
(auth-gated). Confirmed the idiomatic replacement routes resolve and the catalogued
"workaround exists" claim is real.

### Decision — option (c), accept / won't-fix

Operator: "No, leave it alone — close R2 as won't-fix." Executed on the #480 catalog (R2 is a
row in the umbrella issue, not a standalone issue):

- **R2 row** updated to `✅ Accepted — won't-fix (S92)` with rationale + prod-cutover caveat
  inline.
- **Umbrella acceptance line** updated `R1/R2/R3/R5` → `R1/R3/R5` (R2 carries no pipeline fix).
- **Decision-record comment** posted: #480
  [`#issuecomment-4597758427`](https://github.com/martinhbramwell/ESACP/issues/480#issuecomment-4597758427).

**Caveat carried forward:** if prod-tenant bookmarks rely on bare `/tasks`, the cutover fix is
a Frappe **Website Route Redirect** (DB-resident, idiomatic) → `/tasks/list` — not nginx, not
on the generic substrate. Recorded in the #480 body + comment.

## Class

**Decision-only session** — no code, no branch, no commit, no PR. The deliverable is a
recorded won't-fix verdict on one #480 catalog row (institutional memory lives in the GitHub
issue). Not 1:1:1 substantive (no software change) and not a housekeeping bundle. #480
umbrella remains open.

## QA verdicts

**None triggered.** QA trigger ops are commit / merge / push / destructive / `gh issue close`.
This session edited an issue body and posted a comment — no trigger fired. #480 was not closed
(umbrella stays open). No esacp-qa invocation required.

## Counts at session end

- ESACP open: **71**, unchanged (no issue filed or closed; R2 is a catalog row, not an issue).
- LSKB open: **12**, unchanged.
- Sibling trackers (ce_sri 5 / ce_sri_svc 2 / LSV 2 / BaRe 2): unchanged.
- LogiSoluMemory: tip `3949949`, unchanged (no new memory this session).
- dev02 V16 / dev01 V13: untouched (read-only HTTP probe only). Saconsole 4 GiB live.
- TRIVIAL_FIXES.md: unchanged (1 monitor-only).
- ESACP branch: `main`, clean.

## SESSION END audit

- **Forward-tense / orphaned promises:** none. The only forward statement (prod-cutover
  Website Route Redirect) is durably homed in the #480 body row + comment, not left verbal.
- **GH refs:** #480 findings posted as a comment on the issue itself, not only in minutes.
- **PRs:** none opened.
- **Operator doubts:** the "no idea what you're talking about" confusion and the
  evidence-of-use question both resolved in-session and homed in #480; nothing left for
  operator attention.

## Self-classification

Decision-only close — one catalog row (#480 R2) adjudicated won't-fix and recorded; no
software change, no issue count movement. #480 umbrella advances by one resolved row; R6
family (#483), #456, and the fresh-substrate clean run remain.
