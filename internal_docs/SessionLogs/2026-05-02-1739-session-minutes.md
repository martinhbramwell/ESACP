# 2026-05-02 1739 — Session minutes

**Branch:** `test/u6-frappe-dedup-smoke-335` → merged via PR #338 → `main` tip `a0f2ee4`.
**Objective:** Session 2.5 of 4 — close #335 (U6 smoke test: Frappe `(dt, fieldname)` deduplication when source-tree edit + `tabCustom Field` row coexist). Verdict gates the Q-G choice (P1 / P2 / P3) for Session 3.

## Pre-flight

- `bash platforms/kvm/sync_check.sh` → 45 ✅ / 9 ⚠️ / 2 ❌. Failures expected (dev02 shut off per `feedback_one_vm_at_a_time.md`).
- main at `a3aa241`. Working tree carried two staged-but-uncommitted session-log files from prior session (2026-05-02 1452). Per the prior-session pattern (commit `7bffbd4`), committed on `main` as `docs:` housekeeping (`b6042c2`) before branching.
- 29 open issues at session start.
- dev01 reachable; no `bench start` revival needed today.

## What ran

### Pre-branch housekeeping

1. **Committed prior session logs** as `b6042c2` on `main` (`docs: 2026-05-02 1452 session minutes — Session 2 of 4 (#326 closed via PR #336)`). Pushed to origin.
2. Branched `test/u6-frappe-dedup-smoke-335` off main.

### #335 — U6 dedup smoke test (PR #338)

Branch: `test/u6-frappe-dedup-smoke-335`. Merged via PR #338, merge commit `a0f2ee4` at 2026-05-02 21:35:44Z.

**Substrate finding (unanticipated)**:

Auditing the 14 `in_place_core_edit` field-add drifts catalogued in `config/customisation_attribution.yml` revealed that **all 14** already have **dual presence** on the production substrate — the field exists both as a hand-edit in the source-tree doctype JSON **and** as a `tabCustom Field` row. The U6 test scenario is the natural production state, has been for years, and required no insertion to construct. The agenda's prescribed mechanism ("insert a `tabCustom Field` row via UI or `frappe.db`") was unnecessary; the test became a passive observation of existing state.

**Smoke-test script**: `tools/vm_scripts/u6_dedup_smoke_test.py` (70 lines, under the 80-line ratchet). Read-only Frappe metadata probe — no DB mutation. Invoked under bench Python (`/home/erpadm/frappe-bench/env/bin/python3`) with `frappe.init() + frappe.connect() + frappe.clear_cache()`, then `frappe.get_meta(dt).fields` filtered by fieldname for each of 14 probes.

**Verdict — PASS** (14 / 14 probes):

| Evidence type | Result |
|---|---|
| `frappe.get_meta(dt).fields` match count | 1 per probe across all 14 |
| `is_custom_field` on each match | `true` on all 14 |
| DOM `div.frappe-control[data-fieldname]` wrapper count on Customer form | 1 (parity with stock fields `customer_name`, `tax_id`, `customer_type`, `customer_group`, `territory`) |
| Visible label count | 1 per field |

Verdict comment with full evidence: [#335 comment 4364758504](https://github.com/martinhbramwell/ESACP/issues/335#issuecomment-4364758504).

**Side-finding** (durable in the verdict comment + PR #338 body): `is_custom_field=true` on all 14 matches means Frappe credits the `tabCustom Field` row as authoritative; the source-tree edits to standard doctype JSONs are silently **shadowed** at meta-resolution time. The 14 source-tree drifts catalogued under `in_place_core_edit` in `customisation_attribution.yml` are therefore inert in production today — the rendered fields come from the Custom Field rows. This may narrow Phase 5's scope when Q-G is decided.

**Disposition**: Q-G safety prerequisite for P2 / P3 met. Q-G stays open — operator chooses P1 / P2 / P3 on substantive merits at Session 3 entry.

**Acceptance**:

- Smoke-test script runs cleanly under bench Python on dev01; output is structured JSON.
- All 14 probes return `get_meta_match_count: 1`.
- DOM wrapper count = 1 for the test field, identical to stock fields on the same form.
- No state mutation on dev01; script residue removed (`sudo rm -f /home/erpadm/u6_dedup_smoke_test.py /tmp/u6_dedup_smoke_test.py`).
- Anti-spiral size check passes (script trimmed from 91 → 70 lines after first commit attempt was rejected; `tools/size_baselines.json` auto-bumped for the new file by the pre-commit hook).
- PR opened, merged, `mergedAt` non-null before #335 closed (per `feedback_pr_merge_before_session_close.md`). Merge-hash comment posted on #335.

### Substrate quirk worth noting

The `forma_de_pago_preferida` field on Customer is in a collapsed section by default — not visually rendered in the initial form view. DOM-level evidence (wrapper count) was authoritative; visual inspection would have required expanding the section. This is a property of the form layout, not relevant to the dedup question.

## Issues touched

| Issue | Action | Resolution |
|---|---|---|
| #335 | Closed completed | PR #338, merge commit `a0f2ee4` |
| #338 | PR — merged | 2026-05-02 21:35:44Z |

Open-issue count: 29 → 28 (closed #335 only).

## Reminders for the operator

1. **Plan §3 link** — issue #335 spec said "link [the verdict] from §3 of the Phase 5 plan." `~/.claude/plans/phase-5-v14-patch-generator.md` was not modified this session (plan is operator-curated). Suggest updating §3 with the verdict-comment URL before Session 3 starts.
2. **Side-finding for Q-G choice** — all 14 catalogued `in_place_core_edit` field-add drifts have `tabCustom Field` rows that shadow the source-tree edits. The source-tree edits are inert in production. Worth weighing before Session 3 entry: P2 / P3 may not need to do anything special for the source-tree side, since Frappe is already ignoring it.
3. **#337 — U2/U3 disposition** — 24 staged Phase 2 promotion writes still in `ce_sri` / `returnable` / `route_planner` worktrees; 7 of those need `es` (not `es-EC`). Disposition before Phase 5 ships. Earliest natural slot: between this verdict and Session 3 start.
4. **#311**, **#307**, **#280**, **#219**, **#187** etc. — out of scope for the four-session sequence; carried.
5. **Plan-lock holds**: Session 3 = Phase 5 implementation (after Q-G decided); Session 4 = Phase 3 generalised G2.

## Memory updates queued

None. The dual-presence + shadowing finding is already durable in #335 verdict comment + PR #338 body. `feedback_db_resident_customisations_acceptable.md` covers the broader principle; the U6 verdict is a specific empirical confirmation that lives where it was filed (in the issue + commit history), not as a new memory rule.
