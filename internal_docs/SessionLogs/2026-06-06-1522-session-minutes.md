# 2026-06-06 1522 — Session 106 minutes

## Objective (operator-pinned)

Implement the approved S105 plan on `umbrella/v16-clean-run`: **#617 naming-series probe + #618
tenant-Home R-script**, each its own sub-branch → umbrella. **Partially achieved, then
deliberately superseded** — #617 shipped (+ a discovered prerequisite #626); #618 hit a
custom-desk reality that, with operator reflection, triggered a **strategic pivot** (V15 baseline,
MCP-first) that re-scopes #618.

## Class

Mixed. Two substantive 1:1:1 code sub-branches (#626, #617) merged to umbrella; extensive
read-only dev02-V16 investigation; a deep-research run; a strategic decision + memory capture +
plan. ESACP code change = #626 + #617 only. Sister-repo (LogiSoluMemory) updated. **Not an
introspection-sidebar** (ESACP MEMORY.md untouched; the MEMORY.md edited is LogiSoluMemory's).

## What happened

### Pre-flight
sync_check 48✅/9⚠️/0❌ (warnings expected: dormant dev03/target5, manual Chrome check). Issues
ESACP 83 / LSKB 13. Operator pinned **both** #617 + #618.

### #626 (NEW, discovered) — Server Scripts disabled on the V16 substrate → fixed
Authoring R8 surfaced `ServerScriptNotEnabled` on a Sales-Invoice insert. Root cause: V16
`safe_exec` reads `server_script_enabled` **only from `common_site_config.json`** (per-site
ignored), and the substrate set neither — so the tenant's 5 enabled Server Scripts (2 = Sales-
Partner commission DocType events on Sales Invoice) were inert. Filed #626, added
`patch_common_site_config()` (own module, keeps `config_patches.py` at its 80-line baseline),
wired into `cmd_before_install`. Acceptance: live dev02 invoice insert now runs the commission
script. Commit `af5b3ab`, merged to umbrella. esacp-qa: reject (size) → fixed → approve.

### #617 — naming-series probe (R8) shipped
Operator overrode the counter-level idea: **create a real draft Sales Invoice** on the test
series `001-004-.#########` for customer `Compruebalo` + item `Item de Prueba`, assert
name == incremented series. Authored `r8_naming_series_probe.py`; refactored the three
near-duplicate `_run_rN` functions in `v16_post_migrate_fixups.py` into a **data-driven `FIXUPS`
table** (the 80-line cap forced it; scales R9+ to one row). Live dev02: full primitive ran
R1/R3/R8 → invoice `001-004-000000270` created through the commission path. 5 colocated tests
green. Commit `df6246f`, merged to umbrella. esacp-qa approve (commit + §2.2 FF merge).

### #618 — parked after the surface turned out to be custom tenant desk config
Deep dev02 investigation (read-only SQL + Chrome): the V16 desk landing the operator cares about
is **not** the Workspace system — it's the legacy frappe `desktop` page rendering a **bespoke
per-user `Desktop Layout` doctype** (`user` + `layout` JSON; tiles carry `bg_color`/`link`/
`link_type`/`icon`). Also learned: V16 sidebar is **app-grouped** (a workspace's app derives from
`module → Module Def → app_name`; **null-module ⇒ invisible in nav**), V16 lands users on the
**public Home masking private `Home-<user>`**, and the erpnext `leaderboard` Page is **removed in
V16**. Tried four approaches (Inicio workspace → "Mi Rutina" under erpnext → Desktop Icon →
Desktop Layout); operator screen-tested as a real non-Administrator ERPNext user, found none surfaced. **All reverted to
original V16** (deleted experiments + the operator's Desktop-Layout edit + localStorage cache).
**#618 parked.** (Lesson, operator: explore UI affordances — right-click "Edit layout" — before
DB/source archaeology.)

### Strategic pivot (operator-led)
Operator surfaced genuine doubt about whether an AI can become a reliable V16 expert, given the
desk archaeology. Decisions reached:
- **MCP-first sequencing** — build the ERPNext MCP (mission core) before grinding the cutover;
  cutover paused, resumes as beneficiary. (`project_beaverdam_mcp_first_sequencing`.)
- **Deep-research** (task `w96bhqk05`) on the ERPNext MCP landscape → **adopt-and-extend FAC**
  (`buildswithpaul/Frappe_Assistant_Core`; AGPL-3.0, in-app OAuth/audit; CRUD+schema+code/SQL;
  **no** customization-introspection — universal gap across 154 forks; v16 fixable via known
  forks). (`reference_erpnext_mcp_landscape`.)
- **V15 baseline / V16 tracked** — V15 is the Beaverdam baseline (supported to 2027, ecosystem
  targets it, runs on current 22.04/3.10; V16 has a Python-3.12+/PEP-695 + OS-substrate wall).
  Migration decomposes into **two composable scripts (V13→V15 + V15→V16)**; dual-template fleet
  `dev{13,15,16}_NN` with monthly upgrade + regression on both lines. **CloudStack still gates on
  V16.** Plan `~/.claude/plans/beaverdam-v15-baseline-dual-template.md`; end-state memory rewritten.

### Fleet / housekeeping
`dev02` shut down (parked v16 box, frees RAM for dev15_01). r9 file deleted, `feat/618` dropped
(no unique commits; #617/#626 branches kept). Rested on `main`, clean.

## Commits / artifacts
- ESACP: `af5b3ab` (#626), `df6246f` (#617) on `umbrella/v16-clean-run` (pushed; not in main —
  certification later).
- LogiSoluMemory: `a4a4e46` (3 new memories + index), `d6c0c9e` (end-state rewrite). Pushed.
- Issues filed: **#626** (fixed), **#629** (FAC smoke-test), **#631** (v15 template + dev15_01).
- Plan: `beaverdam-v15-baseline-dual-template.md`.

## Open / deferred
- **#631** = next objective (see agenda).
- #629 FAC smoke-test → after dev15_01, re-pointed at v15.
- #480 → re-target V13→V15; re-validate catalog on a v15 instance.
- #618 redo = V15→V16 step (add atajos to Home, DB-only); fix the stale `R9 (#618)` docstring in
  `v16_post_migrate_fixups.py` then.
- dev01/dev02 rename approach (full re-provision vs hosts_map relabel) — deferred until templates exist.
- LogiSoluValidations coverage audit/expansion (credible dual-line regression).
- AGPL-3.0 posture for FAC; V15 dev-baseline ↔ end_state reconciliation (done in memory).
