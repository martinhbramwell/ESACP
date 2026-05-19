# Session Minutes — 2026-04-17

**Objective:** Phase 7 — Dispatcher layer: thin `esacp.py` / `api.py` / `job_worker.py` (#195)

**Result:** ✅ DONE. PR #209 merged as `bf6bdfb`; #195 closed.

---

## What landed

| File | Before | After | Cap | Status |
|---|---:|---:|---:|---|
| `tools/esacp.py` | 811 | 106 | 150 | ✅ |
| `tools/api.py` → `tools/api/__init__.py` | 742 | 53 | 300 | ✅ |
| `tools/job_worker.py` | 227 | 92 | 100 | ✅ |

Three commits on `fix/195-dispatcher-layer`, merged via merge-commit:

1. `58890ac` — `refactor(cli): split esacp.py into tools/cli/ dispatcher layer (#195)`
2. `339c8a7` — `refactor(api): split api.py into tools/api/ package with routes/ (#195)`
3. `9750b07` — `refactor(worker): trim job_worker.py + extract wizard primitive + docs (#195)`
4. Merge: `bf6bdfb`

New structure:
- `tools/cli/*.py` — 12 per-subcommand dispatchers (each ≤80); `_common.py` presentation helpers; `display/` tree + URL-table renderers
- `tools/api/` package — `__init__.py` (app wiring + middleware + exception handlers) + `helpers.py` + `jobs.py` + `routes/*.py` (9 route modules, each ≤80)
- `tools/api_models.py` — Pydantic request models
- 8 new pipeline primitives capturing subprocess that used to live in dispatchers:
  `snapshot_ops`, `local_vm_teardown`, `ansible_provision`, `ansible_playbook_run`, `template_metadata`, `host_health`, `wizard_run`, `preflight/apt_install`
- `tools/verify_phase7.py` — acceptance script (committed in the same PR per [PR-before-session-close](../../memory/feedback_pr_merge_before_session_close.md) + [acceptance-test-required](../../memory/feedback_acceptance_test_required.md))

Pre-commit ratchet updated: `tools/api.py` target limit removed (now a package), `tools/api/` added to CATEGORY_LIMITS at 80.

Subprocess is now banned in dispatchers. Only two documented exceptions:
1. `tools/api/jobs.py` — `subprocess.Popen` for job worker spawn (GH #37)
2. `tools/cli/snapshot_vm.py` — GH #206 deferral

## Acceptance evidence

- `./tools/verify_phase7.py` — all checks green (caps + category caps + subprocess rule + `esacp.py --help`)
- Pre-commit ratchet — green
- Live API smoke: `/api/hosts` (5 hosts), `/api/template/status`, `/api/wizard/recordings`, `/api/jobs`, `/api/vm/saconsole/stop` (hub-protection returns 400)
- `./tools/esacp.py --help` + every subcommand `--help` loads
- `displayConfiguration` + `validateKeys` — produce identical output to pre-refactor
- **Cytoscape Playwright e2e on dev01 (all through refactored endpoints):**
  - Deploy: drag `tpl-erpnext-restored` → `POST /api/provision/erpnext` → `macro/provision.py` → stages 1–9 → Baseline + "ERPNext v13 Logichem DB Restored" snapshots taken (job `3c92f4c2` done, 2026-04-16 23:45Z → 00:13Z, ~28 min)
  - Stop: `POST /api/vm/dev01/stop` — passed 12.4 s, `vm_state → shut off`
  - Start: `POST /api/vm/dev01/start` — passed 9.7 s, `vm_state → running` (memory guard fired)
  - Destroy: `POST /api/destroy/dev01` — job `106d136e` done, all 8 steps executed (WG peer → snapshots → virsh → hosts_map → group_vars → inventory → Ansible hub WG → SOPS keys), `dev01` absent on toshy

## Lessons / confirmations

- The "display_configuration 115 lines > 80" concern from the agenda was resolved by splitting into `cli/display_configuration.py` (17) + `cli/display/config_tree.py` (56) + `cli/display/_meta_sections.py` (55) + `cli/display/url_table.py` (33). All ≤80.
- `tools/api.py` → `tools/api/__init__.py` rename forced ratchet hook updates — target limit removal + CATEGORY_LIMITS expansion. Handled in same PR.
- Full Cytoscape e2e took ~30 min on toshy (mostly stage 7–8 bench/DB restore). Power cycle + destroy is cheap (≤15 s each). The ERPNext v13 template (2026-03-30) is healthy and shaves the stage-1 build completely.
- Playwright parent-shell backgrounding with `&` + `head -N` pipe briefly confused output capture, but the job worker is fully detached (GH #37 design) and completed the provision anyway — confirming that the fully-stateless job model survives arbitrary client-side disconnection.
- hosts_map.yml + friends were mutated by the destroy test; restored via `git restore` before the PR so only the refactor landed.

## Next

Phase 8 — delete dead Gen 1 orchestrators (#196). Detailed agenda: `docs/SessionLogs/2026-04-17-0048-next-agenda.md`.
