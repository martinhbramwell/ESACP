# 2026-06-04 1802 — Session 104 minutes

## Objective (operator-pinned)

**#480 V16-catalog Tier-A/B sweep** — classify every V16-migration concern as Tier A
(blocks cutover) or Tier B (deferred, `defer:post-business`) using the S103 DB-activity
criterion, against the production snapshot dump. Output: each item labelled or surfaced to
the operator. **Achieved.**

## Class

Substantive reasoning + DB measurement, but **no code / pipeline / config change**. Output
is issue-tracker grooming (2 ESACP issues created, 1 LSKB issue created, 1 ESACP issue
closed, 1 re-scoped, 3 grooming comments) + one memory-file update (sister repo). No ESACP
code commit, no PR. **Not a 1:1:1 code session; not an introspection-sidebar** — MEMORY.md
indexing untouched, and carry-forward attrition is faithful close-bookkeeping of items THIS
session resolved (not housekeeping attrition of unrelated aged-out reminders).

## Operator threshold decisions (S103 carry — set this session)

- **Recency window = 365 days** back from snapshot `20260502` → activity ≥ **2025-05-02** is
  "recent". (S103 had *proposed* 90d; superseded.)
- **"Significant" bar = per-item operator classification** — no mechanical count threshold. For
  each item: present `COUNT(*)` + `MAX(modified)` + records-in-window; operator makes the
  Tier A/B call. Overwhelming activity may still self-classify Tier A without asking.

## What happened

### Enumeration (read-only)
Catalog assembled from #480 body + `gh` + memory + the R-script source
(`tools/cli/apply_v16_post_migrate_fixups.py` → R1 #486, R3 #498). Closed children
(R1/R2/R3/R5/R6, #492/#503/#473) are settled; #456 already Tier B (S103). Open targets:
the three #463 omnibus bullets, #457, #466, plus the umbrella's clean-run acceptance gate.
Operator: catalog **assumed complete** (cannot certify exhaustive; further discovery futile).

### Measurement (read-only)
Production snapshot dump was **already extracted** at
`PRODUCTION_20260404/20260502_091736/…-database.sql` (2.16 GB) — no re-extraction, nothing to
clean. No DB client installed; measured by streaming the mysqldump text (Frappe column order
`name, creation, modified, …`). Evidence:

| Backing | Rows | MAX(modified) | Recent (≥2025-05-02) |
|---|---|---|---|
| `tabSeries` | 119 series prefixes (incl. `ACC-GLE-2026-`=10231) | — | — |
| Sales Invoice | 22,507 | 2026-04-29 | 2,395 |
| Stock Entry | 16,249 | 2026-04-29 | 3,550 |
| Payment Entry | 21,886 | 2026-04-29 | 2,225 |
| Delivery Note | 9,858 | 2026-04-29 | 2,596 |
| Sales Order | 9,147 | 2026-04-29 | 2,313 |
| Purchase Invoice | 288 | 2026-02-16 | 76 |
| `tabDashboard` | 13 | 2024-04-29 | 0 |
| `tabDashboard Chart` | 70 | 2024-05-03 | 0 |
| `tabNumber Card` | 56 | 2024-04-29 | 0 |
| `tabWorkspace` | 45 | 2025-02-19 | 0 |

### Classifications (operator)
| Item | Disposition | Home |
|---|---|---|
| Naming Series | **Tier A** (self-classified — significant recent activity) | **#617** |
| Dashboard/Workspace links | **Tier A** (operator override — config-surface importance vs stale recency) | **#618** |
| Serial-No \$0.01 valuation cascade | Promoted out (bucket-2; expands LSKB#10) | **LSKB#32** |
| currentsite.txt deprecation (#457) | **Tier B** (`bench use` migration at cutover) | #457 re-scoped |
| GPG pinentry (#466) | **Excluded** from #480 (controller-bootstrap, no backing table) | #466 noted |
| Homepage faithful rebuild (#456) | **Tier B** (S103, prior) | #456 |

### currentsite.txt — production deletion declined
Operator reported the prod file is empty and said "delete it." **Declined to act on
production** (READ-ONLY hard rule; `currentsite.txt` drives bench default-site resolution).
Re-scoped #457 so the file is removed idiomatically via `bench use` at cutover, never by manual
`rm` on the live server. Operator may delete it directly if desired.

### Actions taken
- **Created** ESACP #617 (Naming Series, Tier A, `umbrella:480`), ESACP #618 (Dashboard links,
  Tier A, `umbrella:480`), LSKB#32 (valuation cascade).
- **Closed** #463 omnibus (completed) — esacp-qa pre-close verdict = **approve** (reopenable,
  no code, all bullets homed).
- **Re-scoped** #457 → Tier B (`umbrella:480` + `defer:post-business`).
- **Comments**: #463 disposition, #466 exclusion note, #480 sweep outcome + addendum.
- **Memory**: `project_v16_migration_triage_criterion.md` updated — thresholds recorded as SET
  (365d / per-item), S104 sweep outcome + override-branch lesson. (No MEMORY.md index change.)

## End state
- **ESACP open: 82** (Senior net **+1** — created #617/#618, closed #463; #457 re-scoped, no
  count change). Delta vs 79 at start is **+2 Junior on_boarding churn** (out of scope).
- **LSKB open: 13** (+1: LSKB#32).
- **#480 critical path no longer empty**: Tier-A `umbrella:480` = **#617, #618**; terminal
  Tier-A gate = fresh-substrate clean-run acceptance (never run). Tier-B = **#456, #457**.
- **dev02 / dev01**: untouched (read-only DB-dump inspection + curl only).
- **Working trees**: ESACP clean apart from Junior's untracked `on_boarding/onBoardingQRcode.png`
  (leave it). LogiSoluMemory: criterion file committed + pushed.
- **sync_check**: 47 pass / 10 warn (dormant VMs, Cytoscape off, Chrome manual note) / 0 fail.

## Decisions
- Triage thresholds **set** by operator: 365-day window, per-item classification.
- Naming Series self-classifies **Tier A**; Dashboard links **Tier A by override** — the
  override branch is the criterion working as designed (lived-knowledge lifts stale-evidence
  items), not a violation.
- Valuation cascade is **bucket-2** → LSKB, dropped from the ESACP platform catalog.
- #466 GPG pinentry is **not a V16 migration defect** → excluded from #480.
- Production `currentsite.txt` **not deleted** — READ-ONLY boundary held; idiomatic removal at
  cutover via #457.

## Session-end audit
Clean — all forward-tense items durably homed (#617/#618/LSKB#32 created with evidence;
#463 closed; #457 re-scoped; #480 outcome recorded; memory updated). One operator-attention
item carried: **#480 next concrete step is the fresh-substrate clean-run acceptance** (Tier-A
terminal gate, never run) — the first non-classification V16 work.
