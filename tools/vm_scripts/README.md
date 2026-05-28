# `tools/vm_scripts/` — VM-side protection + utility scripts

Standalone Python scripts that the pipeline rsyncs to `/tmp/vm_scripts/` on
target VMs (Stage 4 `config_bundle.py:72`). Each one exists to **prevent a
specific failure class** in the substrate-apply / migration flow. Reading
this file first prevents the bypass-shaped failure that motivated
[ESACP#418](https://github.com/martinhbramwell/ESACP/issues/418).

## Cardinal rule

**No raw `bench restore` / `bench migrate` typed at an SSH prompt on a lab
VM.** Always go through a named pipeline primitive — Stage 7
`data_restore.sh` (first-time provision), `BaRe/handleRestore.sh` (re-restore
existing site), or `./tools/esacp.py applySubstrateMigration <host>`
(apply a bespoke-app migration on already-restored data). The primitives
invoke these scripts in the right order; raw bench commands bypass them.

## The scripts

| Script | Failure class prevented | Invocation sites |
|---|---|---|
| `g1_seed_patch_log.py` | Already-applied patches re-running and crashing on the restored DB (substrate-config mismatches like `performance_schema.global_status` visibility — ESACP#398) | `stages/stage_7_data_restoration/data_restore.sh` E1+G1; `BaRe/handleRestore.sh:355-364`; `pipeline/orchestration/substrate_apply.py` |
| `g2_clear_fixture_custom_fields.py` | DocField-vs-CustomField collision during fixtures-import (production has an `in_place_core_edit` DocField that the app's `fixtures/custom_field.json` also defines — `forma_de_pago_preferida` and ce_sri#10 class) | `stages/stage_7_data_restoration/data_restore.sh` G2; `BaRe/handleRestore.sh:355-364`; `pipeline/orchestration/substrate_apply.py` |
| `gpre_strip_definer.py` | Restored backup carrying `DEFINER=<old_user>@<old_host>` clauses that fail on the new DB user — strips to `DEFINER=CURRENT_USER` | `stages/stage_7_data_restoration/data_restore.sh` G-pre |
| `h4a_apikeys.py` | Stale `__Auth` entries from restored snapshot blocking API key regeneration on the new site | `stages/stage_8_app_config/pre_restart_config.sh:38` |
| `h4e_patch_parms.py` | `ce_sri_parms.json` carrying stale `erpnext_api.erpnext_api_key` after H4a regenerates keys — must be patched before `.env` rendering | `stages/stage_8_app_config/post_restart_config.sh:14` |
| `poll_gunicorn.py` | Race condition between supervisor restart and the next stage's HTTP call — polls `/api/method/ping` until 200 | `stages/stage_8_app_config/{pre,post,generic}_restart_config.sh` |
| `u6_dedup_smoke_test.py` | Read-only post-migrate assertion that `(dt, fieldname)` pairs in `tabDocField` ∪ `tabCustom Field` are deduplicated (ESACP#335) | operator-invoked smoke test |
| `r1_recreate_web_page_home.py` | V13 `Homepage` singleton row survives V13→V16 migrate with no V16 render target (DocType upstream-deleted in V14+); recreates a `Web Page` with `route='home'` from runtime-salvaged `tabSingles` fields (ESACP#486, #480 child) | `pipeline/orchestration/v16_post_migrate_fixups.py` |
| `r3_disable_irs_1099_pf.py` | Orphan `IRS 1099 Form` Print Format (Jinja template upstream-deleted) remaining invokable after V13→V16 migrate — sets `disabled=1` (ESACP#498, #480 child) | `pipeline/orchestration/v16_post_migrate_fixups.py` |
| `install_specific/` | Site differentiation (ce_sri config, naming series, test data) — see `tools/CLAUDE.md` § install_specific | `stages/stage_8_app_config/{pre,post}_restart_config.sh` |

## When you're designing a new lab workflow

Before you type `bench` at an SSH prompt, ask: *which of these protections
does this workflow need?* If the answer is "any of them," route through a
pipeline primitive — extend an existing one or add a new orchestration entry
under `tools/pipeline/orchestration/`. Do not hand-roll the runbook.

## How protections get to the target VM

Stage 4 (`config_bundle.py:72`) rsyncs this entire directory to
`/tmp/vm_scripts/`. Stage 4's `verify.py:36-44` checks for it as an
idempotency gate. Substrate-apply primitives that operate outside the normal
provisioning flow (e.g. `pipeline/orchestration/substrate_apply.py`) re-rsync
on demand — the protections must be on disk before the migrate command, not
"some pipeline step rsynced them at some point in the past."
