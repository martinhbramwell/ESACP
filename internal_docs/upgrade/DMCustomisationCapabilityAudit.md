# DM Customisation — Discovery + Promotion Capability Audit

**Issue:** [#313](https://github.com/martinhbramwell/ESACP/issues/313) (gates step 2 onward of `~/.claude/plans/production-v14-migration-prep.md`).
**Plan step:** Step 1.5 — DM Discovery + Promotion Capability Audit (V14 prerequisite).
**Compiled:** 2026-04-28.
**Method:** source-read of every existing pipeline / fixture / G-step mechanism + cross-check against the customisation classes enumerated in `docs/upgrade/CustomisationInventory_v13.md` §10 (held branch `feat/customisation-inventory-v13` @ `c6f7f79`). No new code; verification + design only.
**Memory rule applied:** [`feedback_tactical_vs_consultant_mode.md`](../../../home/hasan/.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/feedback_tactical_vs_consultant_mode.md) — every coverage claim below is backed by a file:line citation, not a memory note.

---

## 1. Why this audit exists

The platform's long-term DM-handling capability requires **two distinct features**:

1. **Discover** — find DM customisations introduced against production since the last externalisation pass.
2. **Promote** — move discovered items into a form (fixture, externalised JSON, equivalent) that survives `bench switch-to-branch` without manual intervention.

The customisation inventory work (#312) revealed that the existing pipeline mechanism — `g2_clear_fixture_custom_fields.py` plus `bench migrate` — is **tactical**: it handles Custom Field fixture re-application collisions, not the general capability set. The 2026-04-27 V13→V14 success on dev02 was on a clean Pseudo-Co substrate and did not exercise this layer.

Without these capabilities verified as long-term features, V14 migration prep cannot continue responsibly. This audit produces a class-by-class verdict and a remediation roadmap. **It does not build the missing pieces** — those become follow-on issues after the operator approves the verdict.

## 2. TL;DR — verdict matrix

Of 11 customisation classes audited, **0 have full coverage on either Discover or Promote**. Apply-at-restore is covered for 1 class (Custom Field), partially for 1 (Property Setter), and absent for 9.

| Class | Discover | Promote | Apply at restore | Verdict |
|---|---|---|---|---|
| Custom Field | ❌ none | ❌ manual | ✅ G2 + `sync_fixtures` | partially covered |
| Property Setter | ❌ none | ❌ manual | ⚠️ `sync_fixtures` only if file `modified` newer than DB row | partially covered (brittle) |
| Custom DocType (`custom = 1`) | ❌ none | ❌ manual | ❌ none | not covered |
| Client Script | ❌ none | ❌ manual | ❌ none (`fixtures/custom_scripts/` mechanism unused) | not covered |
| Server Script (UI-created) | ❌ none | ❌ manual | ❌ none | not covered |
| Custom Print Format | ❌ none | ❌ manual | ❌ none | not covered |
| Workflow | ❌ none | ❌ manual | ❌ none | not covered |
| Naming Series state (`tabSeries`) | ❌ none | ❌ manual | ❌ none | not covered |
| Custom DocPerm | ❌ none | ❌ manual | ❌ none | not covered |
| Translation row | ❌ none | ❌ manual | ❌ none | not covered |
| In-place core JSON / Python edits to `apps/{frappe,erpnext}` | ❌ none | n/a (lives in upstream tree, not DB) | n/a (wiped by `git checkout version-14`) | structurally outside DB-side handling — see §5.11 |

**Two cross-cutting findings** drive most "not covered" cells:

- **F1.** Production's `hooks.py` is older than the externalised fixture set in the current bespoke repos. The fieldname-filter and `"Property Setter"` declarations live in `$BESPOKE_ROOT/ce_sri/ce_sri/hooks.py`, but `$BESPOKE_ROOT/PRODUCTION_20260404/apps/ce_sri/ce_sri/hooks.py:12` reads `fixtures = ["Custom Field"]` (unfiltered, no Property Setter). The promote pipeline has not been exercised end-to-end against production. See §6.
- **F2.** `frappe/modules/import_file.py:127-128, 143-144` skips fixture re-import when the DB row's `modified` ≥ the fixture file's `modified` (for any doctype except `DocType` itself). This is why G2 has to delete-then-let-`sync_fixtures`-recreate; without an equivalent "delete first" pass for every fixture-bearing class, all post-Custom-Field promote attempts are timestamp-gated and brittle. See §7.

## 3. Sources verified

| Source | What it tells the audit |
|---|---|
| `tools/vm_scripts/g1_seed_patch_log.py:21-26` | G1 is a single-patch tactical workaround (`frappe.patches.v12_0.delete_duplicate_indexes`), not a customisation handler. Out of scope. |
| `tools/vm_scripts/g2_clear_fixture_custom_fields.py:32-100` | G2 reads only `apps/*/fixtures/custom_field.json`. Deletes by name + by (dt, fieldname) + clears `tabDocField` collisions. **Filename literal — Property Setter / Print Format / Workflow / Translation files are not touched.** |
| `tools/vm_scripts/gpre_strip_definer.py:21,46-48` | G-pre replaces `DEFINER=<user>@<host>` with `DEFINER=CURRENT_USER`. Permission-related, not customisation. Out of scope. |
| `tools/pipeline/stages/stage_7_data_restoration/data_restore.sh:38-61` | Sequence: E1 (G1 first time) → F (BaRe installApps) → G-pre → G (handleRestore) → G1 again → G2 + `bench migrate`. The only customisation-class handler in the chain is G2; everything else is platform restore + a single inline System Settings patch (G3, lines 63-82) for issue #159. |
| `frappe/utils/fixtures.py:10-28` | `sync_fixtures(app)` calls `import_doc(fixtures_path)` from `frappe.core.doctype.data_import.data_import`. Iterates each app's `fixtures/` dir and calls `import_custom_scripts(app)` separately. |
| `frappe/utils/fixtures.py:31-44` | `import_custom_scripts(app)` upserts `.js` files from `<app>/fixtures/custom_scripts/<DocType>.js` into `tabClient Script`. **No bespoke app uses this directory** (verified — no `custom_scripts` subdir under any of the four `fixtures/` paths). |
| `frappe/modules/import_file.py:117-144` | The timestamp-guard logic. Skips re-import when `migration_hash` matches OR when `is_db_timestamp_latest and doc["doctype"] != "DocType"`. This is F2. |
| `$BESPOKE_ROOT/PRODUCTION_20260404/apps/ce_sri/ce_sri/hooks.py:12` | Production-snapshot fixture declaration: `fixtures = ["Custom Field"]`. Unfiltered. No Property Setter. |
| `$BESPOKE_ROOT/ce_sri/ce_sri/hooks.py:12-33` | Live bespoke-repo fixture declaration: filtered Custom Field (33 fieldnames) + Property Setter. This is F1's other half. |
| `$BESPOKE_ROOT/PRODUCTION_20260404/apps/returnable/returnable/hooks.py:14-16` | `fixtures = [{"dt": "Custom Field", "filters": [...8 fieldnames]}]`. Same in live `$BESPOKE_ROOT/returnable/`. No Property Setter in this app. |
| `$BESPOKE_ROOT/PRODUCTION_20260404/apps/route_planner/route_planner/hooks.py` | No `fixtures` declaration. Same in live `$BESPOKE_ROOT/route_planner/`. |
| `tools/vm_scripts/` directory listing | Only G1, G2, G-pre, plus `h4a_apikeys.py`, `h4e_patch_parms.py`, `poll_gunicorn.py`, `install_specific/`. No G3+ customisation handlers exist. |
| `docs/upgrade/CustomisationInventory_v13.md` §10 (`feat/customisation-inventory-v13` @ `c6f7f79`) | Pass-B SQL set — defines the Discover-side query surface for every class. |

## 4. Methodology — how to read each class verdict

For every class in §5:

- **Coverage row** classifies (1) Discover, (2) Promote, (3) Apply-at-restore.
- **Source** citations are file:line — every `covered` / `partially covered` / `not covered` claim must be traceable.
- **Concrete trace** picks one production example from the inventory and walks it through the pipeline.
- **Remediation proposal** ranks options (extend G2 / new discovery scanner / new promotion helper / accept manual procedure).
- **Operator decision points** are called out where multiple defensible choices exist.

Where a class is fully covered or fully absent, the section is short. The longer sections are where the gap is partial or the remediation choice is non-trivial.

## 5. Class-by-class

### 5.1 Custom Field — partially covered

**Discover:** `not covered`. No script enumerates DB-side `tabCustom Field` rows that don't appear in any app's `fixtures/custom_field.json`. The Pass-B SQL for this exists (inventory §10.2) but is a manual procedure.

**Promote:** `not covered`. No script writes a DB row to a fixture file. The current pattern is operator-side: dev makes the field via UI on production → DM-export → `bench export-fixtures` against production → commit `custom_field.json` to the relevant bespoke app → push.

**Apply at restore:** `covered` for the externalised set. G2 (`g2_clear_fixture_custom_fields.py:71-100`) deletes the DB rows by name **and** by (dt, fieldname) **and** clears colliding `tabDocField` entries (which catches the production case where a DM edit was saved as a standard field rather than a Custom Field). `bench migrate` then re-inserts via `sync_fixtures` with the correct `insert_after` positioning.

**Concrete trace (production example):** `Sales Invoice.access_key` (Data field). DM-created on production → exported to `ce_sri/ce_sri/fixtures/custom_field.json`. On a fresh dev VM restore: Stage 7 G2 deletes `tabCustom Field WHERE name = 'Sales Invoice-access_key'` AND `tabCustom Field WHERE dt = 'Sales Invoice' AND fieldname = 'access_key'` AND `tabDocField WHERE parent = 'Sales Invoice' AND fieldname = 'access_key'`. `bench migrate` re-imports the fixture row. Result: row's `insert_after` matches the fixture (`next_step`), not whatever production had drifted to.

**Remediation proposal:**

- (D) **New discovery scanner** as a long-term feature. Wraps inventory §10.2's Custom Field SQL, runs against a fresh-from-prod-BKP dev VM, emits a delta report listing fields in DB but not in fixtures. Run as part of every external-restore-from-prod cycle (i.e. before the regression suite for V14, V15, V16). New issue.
- (P) **New promotion helper** as a long-term feature. Reads the delta report, generates fixture JSON entries (with the right `dt`/`fieldname`/`insert_after`), and writes them to the most-likely-correct bespoke app's `custom_field.json` (probably ce_sri by default, with `--app` override). Operator reviews the diff before committing. New issue, depends on (D).
- (A) **No change** — G2 is sufficient for apply-at-restore once the externalised set is current.

**Operator decision points:** none — Custom Field is the simplest case.

### 5.2 Property Setter — partially covered (brittle)

**Discover:** `not covered`. Same as 5.1 — Pass-B SQL exists, no automation.

**Promote:** `not covered`. No script. Manual `bench export-fixtures` against the production DB is the current path. Per F1 (production runs older `hooks.py` without `"Property Setter"` in fixtures), `export-fixtures` on production currently does nothing for Property Setters — there is no externalisation pass for this class on production right now.

**Apply at restore:** `partially covered (brittle)`. The current bespoke `ce_sri/hooks.py:32` declares `"Property Setter"` in `fixtures`, so `bench migrate` invokes `sync_fixtures("ce_sri")`, which reads `ce_sri/fixtures/property_setter.json` and calls `import_doc()` per row. Per F2 (`import_file.py:127-128, 143-144`), if the production-restored DB row's `modified` is ≥ the fixture file's `modified`, **the row is silently skipped**. There is no G2-equivalent pre-deletion of Property Setter rows. Whether the fixture overrides DB-side DM edits depends entirely on which timestamp is newer at the moment of `bench migrate`.

**Concrete trace:** `Sales Invoice.amount_eligible_for_commission` Property Setter (visible in inventory §5.1, 24 entries on Sales Invoice; see also §8 of the inventory: production's in-place `apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.json` adds `hidden=1` to this field as a core JSON edit, which is class 5.11). On a fresh dev VM provisioned from production BKP:

1. `handleRestore.sh` restores the DB. `tabProperty Setter` ends up populated from the production dump — including any DM-tweaked `modified` timestamps from production-side UI edits.
2. G2 **does nothing for this row** (G2 only reads `custom_field.json`).
3. `bench migrate` calls `sync_fixtures("ce_sri")` for the Property Setter file in `ce_sri/property_setter.json` (live repo) — but only if `ce_sri/hooks.py` deployed on the VM has `"Property Setter"` in its fixtures list.
4. For each Property Setter row in the fixture: `import_file.py` checks if DB `modified` ≥ file `modified`. If yes (the production DB row was edited recently, fixture file untouched for weeks), the fixture is skipped → DB drift wins.

**Remediation proposal:**

- (D) **Extend the discovery scanner from 5.1** to cover Property Setters. Same delta-report approach.
- (P) **Extend the promotion helper from 5.1** to write Property Setter entries into `ce_sri/property_setter.json`.
- (A) **New `g2b_clear_fixture_property_setters.py`** — exact mirror of G2 for Property Setters. Reads each app's `fixtures/property_setter.json`, deletes matching `tabProperty Setter` rows by name (and by (doc_type, field_name, property) for collisions), then `bench migrate` re-imports cleanly. Acceptable alternative: a generalised `g2_clear_all_fixture_records.py` that introspects each `<app>/hooks.py:fixtures` declaration, finds matching JSON files, and deletes by name across all of them. The generalised form is preferable long-term because it scales to Workflow / Custom DocPerm / Translation if those move to fixtures later. New issue.

**Operator decision points:**

- **D-1** Should the discovery scanner be a standalone script run pre-V14 or a recurring pipeline gate? (Recommendation: standalone for now — pipeline gate after Pass B confirms the steady-state DM-edit rate.)
- **D-2** Generalised `g2_clear_all_fixture_records.py` vs per-class `g2b_*` / `g2c_*`? Generalised reduces maintenance but increases blast radius if a fixture filename convention changes. (Recommendation: generalised, with a per-fixture-file allow-list to prevent accidental cross-app side effects.)

### 5.3 Custom DocType (`custom = 1`) — not covered

**Discover:** `not covered`. Pass-B SQL placeholder in inventory §10.2: `SELECT name, module, app, custom, beta, issingle FROM tabDocType WHERE custom = 1 OR module IN (...)`. No script.

**Promote:** `not covered`. UI-created Custom DocTypes (where `custom=1`) live entirely in the DB. Frappe's standard `bench export-doc` and `bench export-fixtures` mechanism cannot promote them to a bespoke app's source tree — that requires a `bench make-app` or hand-crafted module migration. No bespoke app exposes a `"DocType"` fixture.

**Apply at restore:** `n/a`. `tabDocType` rows where `custom=1` are restored from the production dump exactly as-is. No fixture mechanism applies — the rows survive `bench migrate` because there is no source-of-truth file to compare against.

**Concrete trace:** No example confirmed for production yet (inventory §6 only enumerates code-tree custom doctypes; UI-created ones land in the DB only). Pass-B query needed.

**V14-specific concern:** if v14 changes the `tabDocType` schema (added/removed columns), restoring v13 rows succeeds but the rows may carry stale columns or miss new defaults. The 2026-04-27 dev02 V13→V14 result showed `bench migrate` was idempotent on a clean dev substrate, but did not exercise UI-created Custom DocTypes from production.

**Remediation proposal:**

- (D) **Extend the discovery scanner** to flag UI-created Custom DocTypes (delta against any code-tree doctype dirs).
- (P) **Document a manual procedure** — promotion of UI-created Custom DocTypes is a non-trivial source-tree generation. Probably won't-fix as automated; should be flagged in the discovery report so the operator can decide per-doctype whether to leave it DB-only or migrate to a bespoke app source tree.
- (A) **No mechanism needed** — DB rows survive restore intact.

**Operator decision points:**

- **D-3** Treat UI-created Custom DocTypes as in-scope for promotion automation, or accept them as DB-only artefacts that survive intact across upgrades? (Recommendation: out of scope for promotion. They survive restore; V14-compatibility risk is bounded to schema drift on `tabDocType` itself, addressable per-row in step 4.)

### 5.4 Client Script — not covered

**Discover:** `not covered`. Pass-B SQL placeholder: `SELECT name, dt, view, enabled, script FROM tabClient Script`. No script.

**Promote:** `not covered`. Frappe v13 ships a built-in mechanism: `frappe/utils/fixtures.py:31-44` reads `<app>/fixtures/custom_scripts/<DocType>.js` and upserts each into `tabClient Script`. **No bespoke app uses this directory** (verified — `find $BESPOKE_ROOT -path '*/fixtures/custom_scripts*'` returns empty). So the path-of-least-resistance promote mechanism is structurally available but unused.

**Apply at restore:** `not covered`. Without a `fixtures/custom_scripts/` directory in any bespoke app, `import_custom_scripts(app)` (called from `sync_fixtures`) is a no-op. UI-created Client Scripts live in the production DB; on restore from BKP, the rows survive verbatim, but if the same script needs to be applied to a *fresh* dev VM (`provisionGeneric` mode), there's nothing to seed it.

**Concrete trace:** unconfirmed for production (Pass B). Two file-system signals exist suggesting Client Scripts may be present in production: (a) `ce_sri/install.py` ships a 1391-line install script that includes Client Script seeding (per inventory §3.1); (b) one untracked `crm/number_card/ven/` and one `selling/dashboard_chart/sales_order_analysis_1/` exist in production's `apps/erpnext/` tree, suggesting UI-saved DM activity.

**Remediation proposal:**

- (D) **Extend the discovery scanner** to enumerate `tabClient Script`. For each row, compute a hash of `(dt, view, script)` and check against any `<app>/fixtures/custom_scripts/<dt>.js` files. Output: rows in DB but not in any fixture/custom_scripts directory.
- (P) **Promotion helper writes `<app>/fixtures/custom_scripts/<DocType>.js`**. This uses Frappe's built-in mechanism — no fixture JSON write, just a `.js` file per DocType. Promotion target app needs operator decision (probably ce_sri for accounting/SI scripts, returnable for the returnable doctypes, route_planner for routing).
- (A) **Once `fixtures/custom_scripts/` files exist in a bespoke app**, `sync_fixtures` automatically applies them on every `bench migrate`. No new pipeline step needed. **However**, `import_custom_scripts` does upsert (`frappe/utils/fixtures.py:39-44`), not delete-then-recreate, so it does not have F2's timestamp-guard problem. Cleaner than Custom Field/Property Setter handling.

**Operator decision points:**

- **D-4** Is automation of Client Script promotion in-scope? UI-created Client Scripts are sometimes one-off operator hacks that should not be promoted to a bespoke app at all. Recommendation: discovery scanner emits the list; operator manually promotes the per-DocType ones that are durable, leaves the one-offs as DB-resident with a documented "won't-fix" annotation.

### 5.5 Server Script (UI-created) — not covered

**Discover:** `not covered`. Pass-B SQL placeholder: `SELECT name, script_type, doctype_event, reference_doctype, disabled, script FROM tabServer Script`.

**Promote:** `not covered`. Frappe v13 has no built-in equivalent of `fixtures/custom_scripts/` for Server Scripts. The standard route is to migrate the script body into a bespoke app's hooks (`doc_events`, `scheduler_events`, `whitelist`-decorated function) — which is a non-trivial code transformation, not a JSON dump.

**Apply at restore:** `not covered`. Same as 5.3 — DB rows survive restore but cannot be applied to a fresh dev VM without seeding.

**Concrete trace:** unconfirmed for production (Pass B).

**V14-specific concern:** v14 hardened the whitelist mechanism — `@frappe.whitelist(allow_guest=False)` is now strictly enforced; `@frappe.whitelist()` without an explicit guest argument may fail differently in v14. UI-created Server Scripts that call internal Frappe APIs may break under v14's stricter API surface. Per-script audit needed during step 4 (real-prod-data v14 dry-run).

**Remediation proposal:**

- (D) **Extend the discovery scanner** to enumerate `tabServer Script`. Output: row count + per-row `(name, script_type, doctype_event, reference_doctype)` summary; full `script` body emitted only on `--verbose`.
- (P) **Manual procedure** — automated promotion is not feasible (it's a code refactor, not a data dump). The discovery report becomes a per-row decision: migrate to a bespoke app's hooks, leave as DB-resident, or delete.
- (A) **No mechanism needed** — DB rows survive restore intact.

**Operator decision points:**

- **D-5** Treat Server Scripts as in-scope for V14 audit (step 3 — per-app v14 compatibility) or out-of-scope as operator-managed hacks? Recommendation: in-scope for V14 audit (whitelist mechanism change is a real risk), out-of-scope for promotion automation.

### 5.6 Custom Print Format — not covered

**Discover:** `not covered`. Pass-B SQL: `SELECT name, doc_type, standard, custom_format FROM tabPrint Format WHERE standard = 'No' OR custom_format = 1`.

**Promote:** `not covered`. Two paths exist in Frappe upstream that are not used here:
- A bespoke app could ship Print Format fixtures via `fixtures = ["Print Format"]` declaration and `print_format.json` file.
- A bespoke app could ship custom HTML/Jinja Print Format templates as Python module-bound files (`<app>/<module>/print_format/<format_name>/`).

Neither is used. Inventory §8.2 notes one explicit production-side Print Format DM artefact: `apps/erpnext/erpnext/selling/print_format/pf:_orden_de_venta/` — an in-place core-tree DM edit (class 5.11), not a bespoke-app fixture.

**Apply at restore:** `not covered`. UI-saved Print Formats live in `tabPrint Format` rows + child `tabPrint Format Field` etc.; no fixture file → no `sync_fixtures` apply. Production-side Print Formats survive a real-prod-BKP restore but cannot be re-seeded on a generic-mode dev VM.

**Remediation proposal:**

- (D) **Extend the discovery scanner.**
- (P) **Add a Print Format fixture mechanism to ce_sri.** Declare `fixtures = ["Print Format"]` in `ce_sri/hooks.py` (or a per-format fieldname filter). Then `bench export-fixtures` on production produces `print_format.json`; commit + push to ce_sri.
- (A) **Once the fixture exists**, the same F2 timestamp-guard problem applies as for Property Setter (5.2). Needs the same `g2_clear_all_fixture_records.py` generalisation to handle Print Format alongside Property Setter.

**Operator decision points:**

- **D-6** Are Custom Print Formats stable enough to externalise as fixtures, or do they evolve continuously (operator-side print template tweaks) and so live more comfortably DB-only? Recommendation: discovery scanner first; per-format decision based on age and edit frequency.

### 5.7 Workflow — not covered

**Discover:** `not covered`. Pass-B SQL: `SELECT name, document_type, is_active, workflow_state_field FROM tabWorkflow`. Plus child tables `tabWorkflow Document State` and `tabWorkflow Transition`.

**Promote:** `not covered`. Workflow fixture mechanism exists upstream (`fixtures = ["Workflow", "Workflow State", "Workflow Action Master", "Workflow Transition"]`) but is not declared in any bespoke app's `hooks.py`.

**Apply at restore:** `not covered`. Same shape as Print Format.

**Concrete trace:** unconfirmed for production (Pass B).

**Remediation proposal:**

- (D) **Extend the discovery scanner.** Per-Workflow report including its child rows.
- (P) **Add Workflow fixtures to ce_sri.** Same approach as 5.6.
- (A) **Same generalisation as 5.2/5.6.**

**Operator decision points:**

- **D-7** Same shape as D-6.

### 5.8 Naming Series state (`tabSeries`) — not covered

**Discover:** `not covered`. Pass-B SQL: `SELECT * FROM tabSeries`.

**Promote:** `not covered, but not the right model`. `tabSeries` holds **counter state** (the next number for each prefix), not configuration. Promoting counter state to fixtures would be wrong — it is mutable, per-environment data. The configuration (which prefix is used for which doctype) lives partly in `tabAuto Repeat` and partly in the `naming_rule` field on each DocType, which v13's DocType modifications would carry.

**Apply at restore:** `n/a / by-design from production dump`. On a real-prod-data dev VM, `tabSeries` is restored with counters at production state — that's fine. On generic mode, counters reset to 1, which is also fine.

**Concrete trace:** ce_sri's `install.py` (per inventory §3.1, 1391 lines) likely seeds Naming Series during `before_install`. Pass-B verification needed.

**Remediation proposal:**

- (D) **Discovery scanner emits a row count and the prefix list**, so the operator can see whether new prefixes have appeared since the last externalisation.
- (P) **Manual procedure** — when a new prefix is needed in production, the corresponding `naming_rule` change should be made in the DocType source (a Property Setter on `naming_rule` or a doctype-side patch). The counter itself stays mutable per-env.
- (A) **No mechanism needed.**

**Operator decision points:** none. Naming Series state is the simplest case after Custom Field — the current pipeline behaviour is correct.

### 5.9 Custom DocPerm — not covered

**Discover:** `not covered`. Pass-B SQL: `SELECT name, parent, role, permlevel, ... FROM tabCustom DocPerm`.

**Promote:** `not covered`. Fixture mechanism exists upstream (`fixtures = ["Custom DocPerm"]`) but not declared in any bespoke app.

**Apply at restore:** `not covered`. Same shape as Print Format / Workflow.

**Concrete trace (production example):** inventory §8.1 — production's `apps/frappe/frappe/core/doctype/user/user.json` has a 31-line in-place edit adding an `HR Manager` permissions block. **This is class 5.11 (in-place core JSON edit), not Custom DocPerm**, but it's the right shape — a permission-tree augmentation that should have been a Custom DocPerm fixture and was instead made as a core-tree edit. After V14 strips the user.json edits, the HR Manager permissions disappear unless re-applied.

**Remediation proposal:**

- (D) **Extend the discovery scanner.**
- (P) **Add Custom DocPerm fixtures to ce_sri.** Same approach as 5.6.
- (A) **Same generalisation as 5.2/5.6.**

**Operator decision points:**

- **D-8** Permissions are sensitive — should the promotion helper require explicit operator confirmation per-row, or batch-promote a delta after a single confirmation? Recommendation: per-row diff review before commit (low row count, high blast radius).

### 5.10 Translation row — not covered

**Discover:** `not covered`. Pass-B SQL: `SELECT name, language, source_text, translated_text FROM tabTranslation`.

**Promote:** `not covered`. Two paths exist upstream:
- Fixture: `fixtures = ["Translation"]` + `translation.json` per app.
- File-tree: `<app>/translations/<lang>.csv`. Inventory §8.2 notes production has 2 lines added to `apps/erpnext/erpnext/translations/es.csv` — the file-tree path. That is class 5.11.

**Apply at restore:** `not covered`. Production-side `tabTranslation` rows survive a real-prod-BKP restore. Generic-mode VMs lose them.

**Concrete trace:** the 2 Spanish translation lines in `erpnext/translations/es.csv` are class 5.11 — they will be discarded by `git checkout version-14`. Whether the equivalent rows exist in production's `tabTranslation` is unconfirmed (Pass B).

**Remediation proposal:**

- (D) **Extend the discovery scanner.**
- (P) **Add Translation fixtures to ce_sri.** Same approach as 5.6 — but verify with the operator that translations are stable enough to externalise (they may evolve frequently if the operator hand-tunes Spanish-language UI strings).
- (A) **Same generalisation.**

**Operator decision points:**

- **D-9** Translations as fixtures vs translations as `<app>/translations/es.csv`? Both Frappe-supported. Recommendation: file-tree path for stable bulk translations, fixtures for one-off term overrides. Or accept manual procedure.

### 5.11 In-place core JSON / Python edits to `apps/{frappe,erpnext}` — outside DB-side handling

**Discover:** `n/a — not a DB-side phenomenon.` Pass A of the inventory (§8) already discovered this class via `git status` against the upstream `version-13` baseline:
- 5 modified files + 2 untracked items in `apps/frappe`.
- 18 modified JSONs + 1 modified CSV + 4 untracked dirs in `apps/erpnext`.
- Includes a 1126-line rewrite of `apps/erpnext/erpnext/setup/doctype/sales_partner/sales_partner.json` — the single biggest unknown.

**Promote:** `n/a — must be promoted before V14, by reverting the in-place edit and replacing it with the equivalent fixture/Custom DocPerm/Property Setter form, or accepting a discrete v14 patch.` See inventory §8.3 for the three paths (pre-V14 reconciliation / capture-and-replay / live-with-the-loss).

**Apply at restore:** `n/a — wiped by `git checkout version-14`.` This is the entire reason the class is dangerous.

**This class is structurally outside the discover/promote framework** because it lives in the upstream-app source tree, not in the DB. It is **the single biggest V14 migration risk** per inventory §8.3 and the "biggest unknown" callout for the `sales_partner.json` 1126-line diff.

**Remediation proposal:**

- (D) **A separate "in-place edits inventory" tool** — really just `git -C apps/frappe diff version-13 -- ./` plus the same for erpnext, structured as a per-file report with diff-size column. Inventory §8 already does this manually for the 2026-04-04 snapshot; the tool wraps it for repeatable use against any production-master state.
- (P) **Pre-V14 reconciliation pass on production, operator-side.** For each modified file: decide if it's already covered by an existing fixture (revert in-place edit), needs externalisation first (write a fixture in a bespoke app, push, redeploy, verify, then revert), or is cosmetic/discardable.
- (A) **n/a — class is wiped by V14 by design.**

**Operator decision points:**

- **D-10** When does the in-place edits reconciliation happen? It's the gating prerequisite for V14. Recommendation: file as the **largest** sub-issue post-this-audit, and treat its closure as the explicit V14 go-no-go gate (per the plan file's step 4 / step 6).
- **D-11** `sales_partner.json` 1126-line diff — analyse-and-classify session before reconciliation. Recommendation: dedicated session to read the diff, decide if it represents a doctype redesign that must be replayed as a v14 patch, or a Property Setter/Custom Field combination missed during prior externalisation.

## 6. Cross-cutting finding F1 — production runs older `hooks.py`

**Source citations:**
- `$BESPOKE_ROOT/PRODUCTION_20260404/apps/ce_sri/ce_sri/hooks.py:12` — `fixtures = ["Custom Field"]`. Unfiltered. No `"Property Setter"`.
- `$BESPOKE_ROOT/ce_sri/ce_sri/hooks.py:12-33` — filtered Custom Field (33 fieldnames) + `"Property Setter"`.
- `$BESPOKE_ROOT/PRODUCTION_20260404/apps/ce_sri/ce_sri/fixtures/` — `custom_field.json` only. No `property_setter.json`.
- `$BESPOKE_ROOT/ce_sri/ce_sri/fixtures/` — `custom_field.json` + `property_setter.json` (194 entries per inventory §5).

**Implication:**

The Property Setter externalisation work that the inventory describes (194 entries across 38 doctypes) **has not reached production**. The current production master:
- Does not export Property Setters via `bench export-fixtures` (because production's `hooks.py` doesn't declare `"Property Setter"` in fixtures).
- Has ~194 `tabProperty Setter` rows whose externalised representation lives only in the controller-side bespoke-repo state.
- Will lose those rows' overrides if it ever runs `bench migrate` against the older `hooks.py` deployment **without** a current property_setter.json available — but in practice this risk is bounded because production only runs `bench migrate` during operator-driven upgrade ops.

**Two failure modes this opens:**

- **Failure mode A:** the 194 Property Setter fixture entries in `ce_sri_prod/ce_sri/fixtures/property_setter.json` may be **stale** — they were exported at some past point from somewhere (dev/staging?) and never refreshed. If production's `tabProperty Setter` has drifted since then, the 194-entry fixture is not authoritative.
- **Failure mode B:** the externalisation never went round-trip. If the fixture set was generated from a clean export but the deployed `hooks.py` on production was the older version, then the production DB's Property Setters are ground truth, the fixture file is a snapshot of an unknown-when state, and the two have not reconciled.

**Resolution:** Pass B (DB queries against a real-prod-data dev VM, deferred per inventory §10) is the only way to resolve which version is authoritative. The audit cannot decide this without that data.

**Affected verdicts:** §5.2 (Property Setter) — the "partially covered" rating depends on the fixture file representing production state. F1 means it may not, in which case Property Setter sync_fixtures applies wrong values to a fresh dev VM. Mitigated only when the next bespoke-repo deployment to production happens, followed by a fresh `bench export-fixtures` to refresh the fixture file.

**Operator decision required (D-12):** schedule a **fixture refresh round-trip** before V14:
1. Deploy current `ce_sri/hooks.py` to production.
2. Run `bench export-fixtures` against production.
3. Commit the resulting `property_setter.json` (and refreshed `custom_field.json`) to ce_sri.
4. Now the bespoke repo state matches production.

Without this round-trip, every downstream V14-prep step that depends on "production state matches the fixture set" is built on a possibly-false premise.

## 7. Cross-cutting finding F2 — `sync_fixtures` timestamp guard

**Source citation:** `frappe/modules/import_file.py:117-144` (verified in `$BESPOKE_ROOT/PRODUCTION_20260404/apps/frappe/frappe/modules/import_file.py`). Specifically:

```python
db_modified_timestamp = frappe.db.get_value(doc["doctype"], doc["name"], "modified")
is_db_timestamp_latest = db_modified_timestamp and (
    get_datetime(doc.get("modified")) <= get_datetime(db_modified_timestamp)
)
# ...
# if hash doesn't exist, check if db timestamp is same as json timestamp, add hash if from doctype
if is_db_timestamp_latest and doc["doctype"] != "DocType":
    continue
```

**Implication:**

For any non-DocType record (Custom Field, Property Setter, Print Format, Workflow, Custom DocPerm, Translation), `sync_fixtures` skips re-import when the DB row's `modified` ≥ the fixture file's `modified`. In production, DB-side DM edits routinely produce DB rows newer than the fixture file (the file only gets bumped when an `export-fixtures` round-trip happens, which per F1 is currently rare/non-existent for some classes).

**Why G2 is necessary** (and why a generalised G2 is necessary for every fixture-bearing class beyond Custom Field):

Without pre-deletion, the timestamp guard silently drops the fixture re-import. The end state is:
- Fixture file says: `Sales Invoice.amount_eligible_for_commission` should have `hidden=1`.
- DB row says: `Sales Invoice.amount_eligible_for_commission` is whatever the production DM editor last set.
- `sync_fixtures` reads the DB modified timestamp, finds it newer, and **leaves the DB row alone**.
- Net effect: production drift wins; fixture authority is non-existent.

**G2 escapes this trap for Custom Field by deleting the row first:**
- DB row gone → `frappe.db.get_value(doc["doctype"], doc["name"], "modified")` returns `None`.
- `is_db_timestamp_latest` is then `False`.
- `import_doc` proceeds, inserts the fixture row fresh.

**Affected verdicts:** every "partially covered" or "not covered" cell in §5 where the remediation proposal includes "extend G2 to delete-then-recreate". Without F2 awareness in the remediation, the proposal is a no-op.

## 8. Roadmap — follow-on issues to file

After operator approval of this audit, file the following sub-issues. Each is its own 1:1:1.

| # | Title | Class scope | Priority | Depends on |
|---|---|---|---|---|
| R1 | feat(audit): DM customisation discovery scanner — query Pass-B SQL set against fresh-from-prod-BKP dev VM, emit delta report | All classes 5.1–5.10 | high — gates Pass B and step 4 | — |
| R2 | feat(audit): DM customisation promotion helper — read delta report, generate fixture entries, write to bespoke app | Custom Field, Property Setter, Print Format, Workflow, Custom DocPerm, Translation | medium | R1 |
| R3 | refactor(pipeline): generalise G2 — `g2_clear_all_fixture_records.py` reads each app's `hooks.py:fixtures` declaration and pre-deletes matching rows for every fixture-bearing class | All fixture-bearing classes (currently Custom Field on ce_sri+returnable, Property Setter on ce_sri; expands as R2 adds more) | high — gates Property Setter correctness in restore | depends on D-2 verdict |
| R4 | feat(client-script): adopt `<app>/fixtures/custom_scripts/<DocType>.js` mechanism in ce_sri (and others) | Client Script | medium | R1 |
| R5 | audit(upgrade): in-place core-tree edits inventory + reconciliation plan for `apps/{frappe,erpnext}` | Class 5.11 only | **highest — gates V14** | — |
| R6 | audit(upgrade): `sales_partner.json` 1126-line diff — classify as doctype redesign vs Property Setter/Custom Field combination | Class 5.11, single file | high — sub-issue of R5 | R5 |
| R7 | chore(production): fixture refresh round-trip — deploy current `ce_sri/hooks.py` to production, run `bench export-fixtures`, commit refreshed fixtures | F1 resolution | high — gates Pass B authority | operator-side |

## 9. Operator decision points — consolidated

The recommendations below are advisory; the audit defers to the operator.

| # | Decision | Recommendation |
|---|---|---|
| D-1 | Discovery scanner — standalone vs pipeline-gated? | Standalone for now; promote to pipeline gate after Pass B confirms steady-state DM-edit rate. |
| D-2 | Generalised `g2_clear_all_fixture_records.py` vs per-class `g2b_*` / `g2c_*`? | Generalised, with per-fixture-file allow-list to bound blast radius. |
| D-3 | UI-created Custom DocTypes — in-scope for promotion automation? | Out of scope. They survive restore intact; V14-compat risk bounded to `tabDocType` schema drift, addressable per-row in step 4. |
| D-4 | Client Script promotion automation? | Discovery scanner emits the list; operator manually promotes durable per-DocType ones, leaves one-offs as DB-resident. |
| D-5 | Server Scripts — in-scope for V14 audit (step 3)? | In-scope for V14 audit (whitelist mechanism change is real risk); out of scope for promotion automation. |
| D-6 | Custom Print Formats — externalise as fixtures? | Discovery scanner first; per-format decision based on age and edit frequency. |
| D-7 | Workflows — externalise as fixtures? | Same as D-6. |
| D-8 | Custom DocPerm promotion — per-row confirmation vs batch? | Per-row diff review before commit (low row count, high blast radius). |
| D-9 | Translations — fixture vs `<app>/translations/<lang>.csv`? | File-tree for stable bulk translations, fixtures for one-off term overrides; or accept manual procedure. |
| D-10 | When does the in-place edits reconciliation happen? | Largest sub-issue post-audit; closure is the explicit V14 go-no-go gate. |
| D-11 | `sales_partner.json` 1126-line diff — handling? | Dedicated session to read the diff, decide doctype redesign vs PS/CF combination. |
| D-12 | Fixture refresh round-trip on production — schedule? | Before any Pass B work, so the fixture set on the bespoke repos matches production state. |

## 10. Acceptance against #313

| #313 acceptance criterion | Met? | Evidence |
|---|---|---|
| Document exists, is committed | Pending commit | This file |
| Operator can scan-read in <30 minutes | Yes | TL;DR §2 + roadmap §8 + decision table §9 are scan-readable in <10 min; the per-class detail in §5 is reference material |
| Every customisation class in inventory §10 has a verdict row | Yes | §2 matrix has all 11 classes (10 from #313's table + Custom DocType added per inventory §10.2) |
| Every gap row has a proposed remediation OR an explicit "won't-fix, manual procedure" decision request | Yes | §5 per-class proposals + §9 decision table |
| No new code is written | Yes | Document only |

## 11. Sources of authority for follow-on work

- This document — verdicts and remediation proposals.
- `docs/upgrade/CustomisationInventory_v13.md` (held branch `feat/customisation-inventory-v13` @ `c6f7f79`) — Pass A inventory and §10 SQL set.
- `~/.claude/plans/production-v14-migration-prep.md` step 1.5 — the audit's place in the V14 prep sequence.
- `feedback_tactical_vs_consultant_mode.md` — the lesson behind this audit.
