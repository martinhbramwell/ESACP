# Minutes — 2026-04-07 10:00 — Fixture Collision Fix (#121)

**Objective:** Fix route_planner fixture collision (`forma_de_pago_preferida`) — GH #121.

## Decisions

- ✅ Root cause: handleRestore.sh's "migrate blockers" only deleted `tabDocField`, missed `tabCustom Field`. Collision happened in G's migrate before G2 could clean up.
- ✅ Fix: Replace hardcoded SQL in handleRestore.sh with conditional calls to `g1_seed_patch_log.py` and `g2_clear_fixture_custom_fields.py` — dynamic, covers all fixture fields.
- ✅ Colliding fixture belongs to **ce_sri** (not route_planner) — `forma_de_pago_preferida` is in ce_sri's `hooks.py` fixtures list.
- ✅ G1+G2 in differentiate script retained as idempotent safety nets.
- ✅ All differentiate scripts updated to `git checkout main && git pull` for BaRe (ensures VMs on stale branches get corrected).

## Commits

| Repo | Commit | Description |
|---|---|---|
| BaRe | `7cfe161` | Delegate migrate blockers to ESACP scripts (fixes BaRe#1) |
| ESACP | `34dc6cb` | Merge PR #124 — CLAUDE.md update + differentiate scripts (fixes #121) |

## Acceptance Test

- Refresh on dev02 (job `71c3dce8`): 48 Custom Fields cleared before migrate, zero fixture errors.
- Errors #1 (`session_status`) and #2 (`forma_de_pago_preferida`) eliminated.

## Remaining errors (other sessions)

| Error | Issue | Status |
|---|---|---|
| Encryption key invalid / Social Login 403 | #117 | Open |
| `before_install` API 403 | #122 | Open |
| `frappe-bench-web:` supervisor exit 7 | #123 | Open |
| redis spawn error | #123 | Open |
| ddlViews access denied for erpadm | #116 | Open |

## Deferred

- #120 (session_status patch) — likely already fixed by #107 merge; confirmed in this Refresh (no error). Close with verification.
