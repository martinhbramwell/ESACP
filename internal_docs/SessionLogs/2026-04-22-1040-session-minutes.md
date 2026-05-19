# Session Minutes — #276 cf-mcp-refresh Heredoc Refactor

**Date:** 2026-04-22 ~10:25–10:45 EDT
**Branch:** `fix/276-cf-mcp-refresh-heredoc` (merged to `main` via `09ed5f2`)
**Issues closed:** #276 (objective), #250 (side action — won't-fix per scope clarification)
**Issues opened:** none
**PR:** #283 — merged 2026-04-22T14:41:42Z
**Baseline:** plan file `~/.claude/plans/open-issues-purge.md`; session entered at `main @ eeea2eb`

## Objective

Close #276 by refactoring `tools/cf-mcp-refresh` from bash heredoc-feeding-python to a standalone script, per the CLAUDE.md "Banned Patterns — sed and heredocs-as-code" rule.

## Side action (pre-work) — scope clarification closing #250

User directive mid-session: *"I only care about the production company Logo. Drop all work on the generic site logo. It's a waste of time."* Followed by: *"the express purpose of the generic site is to have a tiny ./handleRestore package for use in the migration ladder to V16, and when testing things like moving a VM from dev to stage. Swapping countries, currencies etc is only to guard against using hard-coded values."*

Actions taken:

- **#250 closed won't-fix** with a close comment capturing the scope rationale (production logo arrives via DB dump on restored runs; generic-mode runs have no branding surface).
- **New project memory** `memory/project_generic_site_purpose.md` codifies the directive as a scope rule — generic-mode provisions are a test substrate (handleRestore V13→V16 ladder + VM-portability / locale swaps), not a product surface. Branding or production-feature gaps default to won't-fix unless they block the ladder or portability tests.
- **MEMORY.md** updated: new Critical-Rules pointer + open-issues line `21 → 20` with #250 close annotation.
- **Plan file** updated: Phase 3A scope narrowed from "Wizard + logo bundle (#181, #250, #271)" to "Wizard bundle (#181, #271)"; the #250-specific risk-mitigation bullet (DB-dump decision) is struck; downstream exit counts shifted by one.

## Objective — #276 outcome

Replaced the 17-line heredoc block in `tools/cf-mcp-refresh` (original lines 56–72) with a 3-line sibling invocation calling a new standalone `tools/cf-mcp-write-tokens.py` (37 lines). Token JSON is piped via stdin (avoids `$RESPONSE` interpolation into a triple-quoted Python literal and `ps aux` exposure); `mcp_auth_dir` + `url_hash` pass via argv. The sibling is located via `BASH_SOURCE`-relative path, so both files must be installed to the same `PATH` directory; `internal_docs/BuildOutProcedure.md` install step updated accordingly.

The inline `python3 -c "…"` one-liners at refresh-script lines 36 (`refresh_token` extract) and 50 (`access_token` validation) are intentionally kept — they are not heredocs and are out of scope per #276. Recorded in the commit body for future readers.

## Files changed (in-repo)

| File | Change |
|---|---|
| `tools/cf-mcp-write-tokens.py` | **NEW** — 37-line standalone stdin→token-writer, shebang + `chmod +x` |
| `tools/cf-mcp-refresh` | Heredoc block replaced with 3-line sibling call (73 → 58 lines) |
| `internal_docs/BuildOutProcedure.md` | Install step now covers both files, with note on colocation requirement |

## Memory + plan updates (outside repo)

| File | Change |
|---|---|
| `memory/project_generic_site_purpose.md` | **NEW** — project-type scope directive; describes where the inert `install_company_logo` path lives and the "leave alone until a neighbouring refactor touches it" posture |
| `memory/MEMORY.md` | +1 Critical-Rules pointer (generic-site scope); open-issues 21 → 19 with #250 won't-fix + #276 closure notes |
| `~/.claude/plans/open-issues-purge.md` | Phase 3A scope narrowed (+ exit-count shift); Phase 1B parenthetical annotated with #276 closure |

## Acceptance verification

- ✅ `./tools/cf-mcp-write-tokens.py` no-args → `usage:` on stderr, exit 2.
- ✅ `echo '{"access_token":"x"}' | ./tools/cf-mcp-write-tokens.py /tmp/nonexistent hash` → `written to 0 version dir(s)`, exit 0.
- ✅ `grep -nE 'heredoc|PYEOF|<<[A-Z]' tools/cf-mcp-refresh` → no matches (exit 1).
- ✅ Installed both files to `~/.local/bin/`; invoked `cf-mcp-refresh` from `PATH` → `cf-mcp-refresh: ✅ token refreshed and written to 2 version dir(s)`, exit 0.
- ✅ `bash platforms/kvm/sync_check.sh` §14 Cloudflare MCP — all four checks green; 0 failures overall.
- ✅ `gh pr view 283 --json state,mergedAt` → `MERGED`, `mergedAt=2026-04-22T14:41:42Z`.
- ✅ `gh issue view 276 --json state,closedAt` → `CLOSED`, `closedAt=2026-04-22T14:41:43Z` (auto-closed by `fixes #276`).
- ✅ `gh issue view 250 --json state` → `CLOSED` (won't-fix, `not planned`).
- ✅ GPG-signed commit `ed2b1c6`, RSA key 9C6BCEA891C518AF1711B05FA232D66FDA9704E8. Pinentry succeeded first attempt.

## PR + merge

- Commit `ed2b1c6` on `fix/276-cf-mcp-refresh-heredoc`, GPG-signed + co-author trailer.
- PR #283 opened with `fixes #276` in body; no CI checks configured, `mergeStateStatus: CLEAN`.
- Merged via `gh pr merge 283 --merge` (branch kept per `feedback_keep_merged_branches.md`). Merge commit `09ed5f2`. #276 auto-closed at 2026-04-22T14:41:43Z.

## State handed to next session

- `main @ 09ed5f2` (pre-minutes-commit); working tree clean.
- Open issues: **19** — #48, #65, #138, #153, #156, #157, #181, #187, #202, #219, #220, #223, #225, #235, #240, #241, #271, #278, #280.
- Plan next hop: **Phase 3A** — Wizard bundle (#181, #271 piggyback), first matrix-touching phase. Runs 03 + 06 with B03/B06 regeneration.

## Reminders to user (unresolved concerns)

1. **Phase 3A is matrix-touching.** Back up `platforms/kvm/golden_backups/B03.tar.*` and `B06.tar.*` to `platforms/kvm/golden_backups/archive/` **before** opening the 3A branch, not during.
2. **The inert `install_company_logo` upload path stays in the tree.** Per the generic-site scope directive + explicit "waste of time" framing, no dedicated cleanup issue was filed. The dead code (in `after_restart/logo.py` + `stage_3_connectivity/cesri_secrets.py:_collect_static_files` + `cesri_secrets.py:52`) will be deleted in passing whenever a future refactor naturally touches one of those files. `memory/project_generic_site_purpose.md` holds the standing instruction.
3. **Umbrella-branch policy still has no live instance.** Policy landed in Phase 2C (#236) but has not been exercised. First multi-session refactor meeting the trigger criteria (likely ERPNext v13→v16 upgrade, or a matrix-rewrite sweep) will be the first real test — watch for rough edges on first use.
4. **Stale-install hazard for operator tooling.** `~/.local/bin/cf-mcp-refresh` was dated 2026-03-29 at session start — 24 days drifted from the repo canonical. The install command in `BuildOutProcedure.md` is correct but manual; `sync_check §14` tests behaviour, not version. If the operator-local copy silently diverges again, a future bug could land. Worth considering a version-stamp check as a future hardening (not a current blocker).

## File trail

- Commit (fix): `ed2b1c6` on `fix/276-cf-mcp-refresh-heredoc`
- Merge commit: `09ed5f2`
- PR: <https://github.com/martinhbramwell/ESACP/pull/283>
- Closed issues: <https://github.com/martinhbramwell/ESACP/issues/276>, <https://github.com/martinhbramwell/ESACP/issues/250>
- Plan file: `~/.claude/plans/open-issues-purge.md` (Phase 3A scope narrowed, Phase 1B follow-up annotated)
- New memory: `memory/project_generic_site_purpose.md`
- MEMORY.md: Critical-Rules pointer + open-issues 21 → 19
- This minutes: `internal_docs/SessionLogs/2026-04-22-1040-session-minutes.md`
- Prior session minutes: `internal_docs/SessionLogs/2026-04-22-0801-session-minutes.md` (Phase 2C umbrella-branch policy)
