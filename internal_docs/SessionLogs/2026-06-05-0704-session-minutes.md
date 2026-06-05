# 2026-06-05 0704 — Session 105 minutes

## Objective (operator-pinned)

**Characterize #617 (Naming Series) + #618 (Dashboard quick links) and fold both INTO the
#480 V13→V16 clean-run acceptance** — operator's call: they were never truly separable from
the acceptance; the S104 catalog split was a tracking artifact. Scope chosen: *characterize +
plan* (author + run next session). **Achieved.**

## Class

Read-only characterization (dev02-V16, SSH + browser) + planning. **No ESACP code / pipeline /
config change.** Output = 2 issue comments (#617/#618 re-grounded from "characterize" to
disposition), 1 plan file (`~/.claude/plans/v16-clean-run-617-618.md`), 1 sister-repo memory
update, session-log docs. **Not a 1:1:1 code session; not an introspection-sidebar** (MEMORY.md
indexing untouched; no carry-forward attrition of unrelated aged-out reminders).

## What happened

### #617 Naming Series → PROBE-ONLY (no fix-script)
V16 changed only the **admin surface**: `Naming Series` DocType gone → `Document Naming
Settings` + `Document Naming Rule` (the V14+ rename the operator sensed). Autoname machinery
intact: 119 `tabSeries` counters survived (2026 series live); every major transactional doctype
still `autoname='naming_series:'` / `naming_rule='By "Naming Series" field'`, custom series
pinned by Property Setters (survive migration; incl. bespoke Sales-Invoice `001-002-.#########`).
→ Folds into clean-run as a create-doc/assert-increment **probe**.

### #618 Dashboard quick links → REAL render-time defect, reproduced + root-caused
- **Screen repro (Administrator, dev02-V16):** `/app/home` lands on the **stock public `Home`**
  (4 core shortcuts); tenant custom quick links **absent**.
- **Root cause:** V14+ public/private workspace model. Customizations survived into **private
  per-user `Home-<user>`** workspaces (e.g. `Home-Administrator` = 8 shortcuts incl. `Botellon`,
  `Returnables Batches`, `Planificador de Rutas`); V16 surfaces the **same-titled public `Home`**
  and masks them. Private workspace reachable by direct URL (`/app/home-administrator` renders the
  custom buttons), not from sidebar/landing.
- **Not** data loss (records + `content` JSON intact), **not** app-incompat (all targets resolve;
  `returnable` + `route_planner` installed). Bucket-2 entanglement moot (apps installed at cutover;
  Plan B parked).
- → Real fix; DB-resident R-script over `tabWorkspace`.

### Mechanics of the fold (operator's ask satisfied)
Both plug into `tools/pipeline/orchestration/v16_post_migrate_fixups.py` via `run_fix_script`
(the same R1/R3 contract: `[PROBE] key=value` + EXPECTED set + CHANGED marker), which the
clean-run acceptance invokes after `bench migrate`. So "see naming series + quick links AS PART
OF the clean run" is satisfied mechanically — the acceptance fails if either probe fails.

### Read-only characterization method
SSH to dev02 (WG `10.10.0.17`) + standalone Python probe scripts run via the bench venv
(no heredocs/inline code per banned-patterns); browser repro via Chrome MCP. Lab Administrator
login = `erp_user_pwd` from `build_secrets.sops.yml` (never prod). dev02 apps.txt confirmed:
frappe, route_planner, ce_sri, sales_partner_commissions, returnable, erpnext.

## Operator decisions
- Fold #617 + #618 into the #480 clean-run acceptance (not separate sessions).
- Session scope = **characterize + plan**; author + run = next session.
- #618 fix shape = **(B) preserve per-user** — surface each user's private `Home-<user>` on V16
  (de-collide title / demote public `Home` / set private as default landing — mechanism picked
  at authoring). Not consolidate-to-public, not rebuild.

## End state
- **ESACP open: 82** (no count change — 2 comments, no create/close). **LSKB open: 13** (no change).
- **#617** re-grounded: probe-only. **#618** re-grounded: real fix, root cause known, decision B.
- **Repo: clean** apart from Junior's untracked `on_boarding/onBoardingQRcode.png` (leave it).
  This session commits only session-log docs to `main`. LogiSoluMemory: triage-criterion file
  updated (commit + push).
- **dev02:** read-only inspection + one read-only browser login; no state change. `/tmp` probe
  scripts left on dev02 (disposable). **dev01:** untouched.
- **sync_check:** 48 pass / 9 warn / 0 fail (transient #401 WG-handshake on first run, clean on
  re-run).
- **Plan:** `~/.claude/plans/v16-clean-run-617-618.md` (umbrella `umbrella/v16-clean-run`).

## Session-end audit
Clean — both children re-grounded with evidence; decision B captured; plan written; memory
updated. Forward item: **S106 implementation** on `umbrella/v16-clean-run` (author #617 probe +
#618 R-script, wire into `v16_post_migrate_fixups.py`, then the #480 clean-run acceptance).
