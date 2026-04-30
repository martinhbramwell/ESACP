# 2026-04-30 1641 — Session minutes

**Branch:** `main` (design branch `design/in-place-core-edits-classifier-317`
cut speculatively then abandoned — design sessions don't need branches per
the 1453 precedent, `a3b03f7`).
**Objective:** Design and lock Phase 4 — in-place core-tree edits classifier
(#317) — by running domain research first (spot-check, diff landscape
survey, Frappe source-grounded fingerprints), then writing the locked
design into plan §7.
**Type:** Plan-only session per `feedback_plan_before_code.md`.

## What ran

### Pre-flight

- `bash platforms/kvm/sync_check.sh` → 46 ✅ / 8 ⚠️ / 2 ❌. Both ❌
  expected per `feedback_one_vm_at_a_time.md` (dev02 deliberately off,
  16 GiB toshiba RAM constraint).
- `gh issue list` → 29 open. #317 confirmed open and in scope.
- Working tree clean; main at `a3b03f7`.

### Spot-check (per #317 2026-04-29 13:33 comment)

Verified `user.json` HR Manager claim against
`$BESPOKE_ROOT/PRODUCTION_20260404/apps/frappe`:

```text
diff vs upstream/version-13: +28 / −3 = 31 unified-diff lines
substance: 2 Custom-DocPerm-equivalent permission objects (23 lines)
noise:    8 lines (modified timestamp, "states": [] removal, EOF newline)
HR Manager present in worktree (lines 705, 718)
HR Manager absent in upstream/version-13
```

Audit §5.9 prose approximately correct; **no #317 body correction
needed**. Spot-check verdict recorded in #317 comment.

Sales_partner.json (audit §8 "1126-line rewrite") additionally
sanity-checked: actual diff is `+199 / −881`, deletion-dominant —
matches operator's earlier "~682-line deletion" recount, not the audit
prose. Phase 4 will emit this as `discardable_core_edit`, sidestepping
the discrepancy entirely.

### Diff landscape survey

| App | Tracked-modified | Untracked trees |
|---|---|---|
| `frappe` | 5 files | 1 (`frappe/custom/dashboard_chart/`) |
| `erpnext` | 18 files (incl. 1 translation CSV) | 4 |

Per-file diff sizes catalogued. Two outliers:
- `party_type.json` — `+62 / −153` (net deletion).
- `sales_partner.json` — `+199 / −881` (net deletion).

Both fall into rule 4 (`discardable_core_edit`).

### Source-grounded fingerprints

Read Custom DocPerm + Property Setter doctype field lists from
`PRODUCTION_20260404/apps/frappe`:

- **Custom DocPerm**: `role`, `parent`, `permlevel`, `if_owner`, plus
  the action-check set (`read`, `write`, `create`, `delete`, `submit`,
  `cancel`, `amend`, `report`, `export`, `import`,
  `set_user_permissions`, `share`, `print`, `email`, `select`).
- **Property Setter**: `doctype_or_field` (DocType vs DocField),
  `doc_type`, `field_name`, `property`, `value`, `property_type`,
  `default_value`, `row_name`.

The HR Manager objects in `user.json` map 1:1 to Custom DocPerm rows.

### Plan §7 Phase 4 lock

Edited `~/.claude/plans/customisation-discovery-promotion.md` §7,
replacing the placeholder with the full locked design:

- Substrate model (production-master worktree, env-var override).
- Classification rules (7 in priority order; first match wins).
- Module breakdown (8 SUT + 7 tests, each ≤50 lines).
- Dispatcher integration (extend `AuditConfig.core_tree_root`).
- Acceptance criteria carried forward to implementation session.
- Out-of-scope items re-stated.

### #317 comment

Design-lock comment posted: `issuecomment-4356005616`. Includes
spot-check verdict, diff-landscape table, source-grounded fingerprints,
classification rules, acceptance criteria, Phase 2 hand-off note.

## Outcome

- **#317 design locked.** Plan §7 Phase 4 placeholder replaced.
- Implementation is a single self-contained session against
  `feat/in-place-core-edits-classifier-317`, no upstream blockers.
- No code shipped this session; no PR.
- Working tree clean on main; `design/in-place-core-edits-classifier-317`
  branch abandoned (no commits made on it).

## Issues touched

- **#317** — design lock comment, plan §7 updated. Stays OPEN for
  implementation. No `fixes` keyword used; the issue closes when the
  implementation PR merges.

## Memory rules applied

- `feedback_domain_research_first_for_cross_major.md` — research-first
  this session (spot-check, landscape survey, Frappe source).
- `feedback_tactical_vs_consultant_mode.md` — verified audit prose
  before treating as load-bearing; sales_partner.json claim caught.
- `feedback_plan_before_code.md` — plan locked; implementation in a new
  session.
- `feedback_pr_merge_before_session_close.md` — N/A (no PR).
- `feedback_sut_frozen_tests_unlimited.md` — design specifies test
  fixtures colocated under `fixtures_core_edits/`, frozen at design time.
- `feedback_tests_with_code.md` — tests colocated, no separate `tests/`
  tree.
