# 2026-04-28 1018 — Session minutes

## State at session start

- Pulled from agenda `2026-04-28-0736-next-agenda.md` — direction shift to production V13→V14 logged previous session
- main tip: `dc643db`, clean tree
- Sync_check: 45 ✅ / 9 ⚠️ / 2 ❌ — both ❌ are the dev01 carve-out per #278 (known/expected); no new failures
- Open issues: 24
- Operator role-cue: ERPNext Senior Consultant (explicitly invoked — drove the framing of the work + the mid-session pivot to #313)

## Objective stated

Step 2 of `~/.claude/plans/production-v14-migration-prep.md` — produce `docs/upgrade/CustomisationInventory_v13.md`. New GH issue filed at session start per 1:1:1 discipline.

## What happened

- **Issue #312 filed** at session start (customisation inventory).
- Branch `feat/customisation-inventory-v13` cut from main.
- File-system survey across `$BESPOKE_ROOT/{ce_sri,route_planner,returnable,BaRe,ce_sri_svc}` + `$BESPOKE_ROOT/PRODUCTION_20260404/` (snapshot 2026-04-04).
- **Pass A inventory** drafted and committed to branch as `c6f7f79` — 553 lines, 12 sections, GPG-signed.
- **Critical finding (§8)** surfaced during snapshot diff: production-master `apps/{frappe,erpnext}` carries 21+ uncommitted Developer Mode edits not covered by externalisation fixtures. Biggest single item: `sales_partner.json` 1126-line diff vs upstream version-13.
- **Operator pivot**: questioned whether `g2_clear_fixture_custom_fields.py` (cited by me from memory note) is a long-term capability or tactical fix. Operator instruction: do not proceed with V14 prep until DM discovery + promotion completeness is resolved.
- **G2 source-read** confirmed: tactical fix scoped to Custom Field collisions only. Per-class coverage table verified against the inventory's §10 SQL set.
- **Issue #313 filed** capturing the audit + design work (DM Discovery + Promotion Capability Audit — V14 prerequisite).
- Plan file `~/.claude/plans/production-v14-migration-prep.md` updated: Step 1.5 inserted, "What's already proven" caveated, Step 2 pre-req'd, status table refreshed.
- Memory: `feedback_tactical_vs_consultant_mode.md` saved; MEMORY.md pointer added.
- **Branch HELD local** — not pushed, no PR opened. Inventory PR awaits #313 verdict.

## Issues opened

- **#312** — `docs(upgrade): customisation inventory for production v13 (step 2 of v14 migration prep)` — OPEN, branch held
- **#313** — `audit(upgrade): DM customisation discovery + promotion — verify completeness as long-term capability (V14 prerequisite)` — OPEN

## Issues commented

- **#312** — held-branch status comment with §8 critical finding pointer + #313 link (`issuecomment-4338205743`)

## PRs opened

None. Inventory branch is local only.

## Commits

- `c6f7f79` (on `feat/customisation-inventory-v13`) — `docs(upgrade): add customisation inventory for production v13` (`fixes #312`)
- This minutes/agenda commit (on main) — to follow

## Memory artefacts

- New: `memory/feedback_tactical_vs_consultant_mode.md` (V14-prep precedent — read cited mechanisms in source before treating as load-bearing)
- Updated: `memory/MEMORY.md` — Critical Rules section now references the new feedback memory

## Plan-file changes

`~/.claude/plans/production-v14-migration-prep.md`:
- "What's already proven" gained G2-tactical caveat (line 18)
- **Step 1.5 inserted** between Step 1 (#307) and Step 2 — "DM Discovery + Promotion Capability Audit (V14 prerequisite)" tracked by #313 (line 34)
- Step 2 prepended with "Pre-req: Step 1.5 audit verdict" (line 57)
- Status table refreshed with row 1.5 + amended dependencies (lines 156–162)

## Direction shift logged

Operator clarified: an ERPNext customisation handling pipeline must have **two capabilities** — (1) discover DM customisations introduced against production, (2) promote them to upgrade-safe form. The pre-existing G2 step is tactical (Custom Field collisions only); neither (1) nor (2) is implemented as a designed feature. V14 migration prep cannot proceed responsibly until those capabilities are verified or designed. Captured in #313 + plan-file Step 1.5 + new feedback memory.

The 22-day-old memory `project_si_custom_fields_baseline.md` ("13/13 externalised, apps/erpnext 100% stock") is correct only for the dev/staging substrate; production-master itself was never reconciled. This was the load-bearing assumption that justified V14 dev02 success generalising to production. It does not.

## Reminders carried forward (also in next agenda)

1. **Inventory branch `feat/customisation-inventory-v13` @ `c6f7f79` is HELD local.** Don't merge, don't PR, don't pull main into it without explicit reason — until #313 verdict.
2. **§8 finding lives only on a held branch.** 21+ DM edits in production-master apps tree (incl. 1126-line `sales_partner.json` rewrite) is a real V14 blocker — currently not visible to `gh issue list`. #313 references it as out-of-scope; a separate ticket promised once #313 verdict lands.
3. **§11 follow-up list (6 items)** committed on branch; no GH issues filed yet — most deferred to step 3/4. The in-place-core-edits item is the V14 blocker, not a step 3/4 matter.
4. **Two-capability frame is new** — discover/promote framing isn't in the codebase or memory before this session. Plan file + #313 body carry it; next session re-load both.
5. **dev02 on V14, dev01 shut down.** Pass B / Step 4 will require dev02 shutdown first per `feedback_one_vm_at_a_time.md`.
6. **Production is READ-ONLY** from this controller — unchanged.

## Acceptance

Step 2 deliverable (Pass A) committed locally — meets the "operator can scan-read in under 30 minutes" acceptance bar. Pass B + branch merge held pending #313. Step 1.5 (#313) is the new gate.
