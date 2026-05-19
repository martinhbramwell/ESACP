# 2026-05-05 0730 — Session 8 minutes (#346 → #347 root-cause + fix → e2e validated)

## Stated objective at session start

Per `2026-05-04-1605-next-agenda.md`: investigate **ESACP#346** (V13 error operator noticed at Session 7 close — placeholder body, details pending). Discovery session: capture the real error, reproduce if possible, decide scope.

## How the session actually went

Operator surfaced the #346 details: Sales Invoice IVA tax not calculating correctly on dev01. Operator directed: shut down dev01, build a fresh fully-customized V13 on dev02 via the topology UI, validate the anomaly there.

The dev02 build failed at **Stage 7 G2 `bench migrate`** — `pymysql.err.ProgrammingError: (1064, 'You have an error in your SQL syntax... near \'\'fieldname\': "\'barrio\'", \'fieldtype\': "\'Link\'"...\' at line 2')`. Operator escalated to "5 alarm fire — track down the cause and get it working, no other priority."

### Root-cause investigation

`tools/pipeline/stages/stage_7_data_restoration/__init__.py:89-90` reports `r.stderr.strip() or r.stdout.strip()` — surfaced only the last stderr line (a benign `pkg_resources` deprecation warning). The real failure was in stdout, dropped on the floor. Bypassed by SSH-into-dev02 via toshy ProxyJump (cloud-init `you` user, since stage 2's wireguard install had silent-warned).

Bench-log timeline showed `bench migrate` crashed during route_planner DocType update, in `sync_fixtures()` → `import_doc()` → `INSERT INTO tabProperty Setter`.

### What broke

- `route_planner/route_planner/fixtures/property_setter.json` (commit `e9b7b7f`, 2026-05-02, this hand) contained two entries for `Address-fields[barrio]` and `Address-fields[delivery_route]` with `value` as a nested JSON object. Frappe's importer stringifies the dict via Python `repr()` into the TEXT column, producing malformed SQL.
- Provenance traced through Phase 4 / Phase 2 audit pipeline: `core_diff_property._additions()` (line 13-14) lifted `af[fn]` (the parsed field-def dict) into `row_data["value"]`. `promote_fixture_json.compose()` writes `row_data` verbatim with `json.dumps`, so the dict landed as a nested object.
- Deeper finding: `_v14_compose_property_setter.py:6-7` documents the design rule: "Used for top-level Property Setter changes (real properties like `naming_rule`, NOT `fields[X]` additions — those route to `_v14_compose_custom_field.py`)." Phase 4's classifier was emitting Property Setter drifts for what the V14 generator recognises as Custom Fields. dev02 SQL probe confirmed: production has these as `tabCustom Field` records, NOT `tabProperty Setter`.

### Operator-visible re-framing mid-session

Mid-investigation, parent over-narrated and asked the operator to pick between technical taxonomy paths. Operator pushed back: "I am that family member. Do I want you asking me what to do with it?" Memory entry filed (see below). Parent shifted to consultant-action mode: investigate, decide, fix, verify, report — without asking for menu-choice approvals on engineering taxonomy.

### Fix landed

| Repo | Branch / commit | Status |
|---|---|---|
| ESACP | `fix/347-route-fields-additions-to-custom-field` | **PR #348 merged** (`2f64be1`) — squash, branch retained per `feedback_keep_merged_branches.md` |
| route_planner | `wip/2026-03-31` → `e87a64e` (direct push) | Empty broken `property_setter.json`, populate `custom_field.json` with 2 Address Custom Fields matching production tabCustom Field |

Code changes in ESACP:
- New `tools/customisation_audit/core_diff_added_field.py` — emits Custom Field drifts for `fields[X]` additions
- `core_diff_property.py` — restricted to true top-level prop additions; no longer scans `fields` array
- `core_diff_classifier.py` — `added_field` runs before `property` in priority order
- `test_core_diff_added_field.py` (new), `test_core_diff_property.py` (updated)
- `pre_commit_size_check.py` — added `core_diff_added_field.py` to TARGET_LIMITS @ 50 (per esacp-qa condition on PR-merge verdict)

Two commits on the branch (squash-merged): `463b1d3` (the fix) and `843fb68` (the ratchet entry + docstring trim to 49 lines).

### Acceptance evidence

Local on dev02 (controller-side patch then run):
- G2 cleared 49 Custom Fields by name + by (dt, fieldname) + colliding DocField entries
- `bench migrate` exit 0, "Updating customizations for Address" appeared
- Both Custom Fields verified in DB with correct shape

Full e2e via topology UI (Playwright `quicktest-dev02-rebuild.spec.js`, deleted post-session):
- Provision job `0127021a`: **done** in 31.1 min
- Stage 7 G2 clean
- Final snapshot `ERPNext v13 Restored Baseline` taken
- HTTPS `https://dev02.iridium.blue` → **HTTP 200** in 0.98s
- Operator confirmed IVA tax-calc correct on the fresh build → original anomaly was dev01-state-specific, not code

### Orthogonal observation

Operator submitted the test invoice to SRI; got `AxiosError: read ECONNRESET` at 06:37:01. This is the known #343 pattern (suspended Session 7), exogenous to our system, addressed by parked `ce_sri_svc#3`.

## Issues touched

| # | Action |
|---|---|
| #346 | **Closed** — premise resolved (anomaly was dev01-state, not code) |
| #347 | **Filed + Closed** — root cause + fix (PR #348 merged) |
| #348 | **Merged** to main, `2f64be1` |
| #349 | **Filed** — bug(stage-7): error reporter masks real failures (last-stderr-line vs full stdout/stderr) |
| #350 | **Filed** — bug(stage-2): wireguard-tools apt-fetch failure tolerated as `[WARN]` — should hard fail or retry |

## QA verdicts

| Trigger | Verdict | Notes |
|---|---|---|
| ESACP commit `463b1d3` | approve-with-conditions | Pre-commit ratchet would block on `core_diff_property.py` 47→50 — trimmed to 45 before commit |
| ESACP push `463b1d3` | approve | All gates pass |
| route_planner commit + push `e87a64e` | approve-with-conditions | Wanted acceptance test before push; satisfied via local-on-dev02 G2+migrate validation, with full e2e to follow post-push (catch-22 — pipeline clones from remote) |
| ESACP PR #348 merge | approve-with-conditions | New module untracked by ratchet — addressed via follow-up commit `843fb68` |

## Memory updates written

Two new feedback memories from this session, written to local memory directory `~/.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/` (outside the repo) and indexed in MEMORY.md:

1. **`feedback_consultant_not_peer_engineer.md`** — When operator frames a problem operationally, default to consultant-action mode (investigate, decide, fix, verify, report). Don't ask non-technical operators to pick between engineering taxonomy paths. Trigger: 2026-05-04 mid-#347 investigation when parent presented 4 ranked options; operator's response: "Do I want you asking me what to do with it?"

2. **`feedback_check_size_baselines_at_commit_time.md`** — Two pre-commit ratchet collisions tonight (`core_diff_property.py` 47→50, `core_diff_classifier.py` 25→29). Pattern: when a commit touches files in TARGET_LIMITS, check `tools/size_baselines.json` first and trim docstrings/comments to fit BEFORE running `git commit`.

## Files at session-end

- `internal_docs/SessionLogs/2026-05-05-0730-session-minutes.md` — this file
- `internal_docs/SessionLogs/2026-05-05-0730-next-agenda.md` — Session 9 agenda (Playwright regression suite design)
- `internal_docs/qa-log.md` — appended 5 verdicts from this session

## Estimated wall-clock

~10.5 hours (operator-active intervals): 2026-05-04 21:00 EDT through 2026-05-05 07:30 EDT. Long session — single objective resolved end-to-end.
