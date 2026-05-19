# Session Minutes — 2026-04-19 16:22 — #239 P1–P5 scrub plan

**Branch:** `fix/conduct-scrub-client-name`
**Objective:** Produce the execution plan for issue #239 — client-name scrub across SUT / docs / binary content. **Plan-only session; no SUT code changes.**
**Outcome:** Plan complete. Plan file at `~/.claude/plans/conduct-scrub-client-name.md`. Three follow-on issues filed (#240, #241) or referenced (#239). No PR.

---

## Framing decided

Goal reframed mid-session from *secret-hiding* to *generic-platform appearance*. Consequences carried through every P-section:

- Git history, PR titles, merge commits: **untouched.**
- Historical session logs (`docs/SessionLogs/<older-date>-*`): **untouched** by default.
- Acceptance is human-judgement reader-test, not grep-zero. Diagnostic grep allows documented carve-outs.
- Committed default DNS zone: `yourpublic.work` (owned by project owner, routable).
- Replacement tokens: `company_specific` (snake), `company-specific` (kebab) — used only where extraction to config is architecturally required; most sites use deletion or natural generic rephrasing (e.g., "Restored ERPNext" with the "Logichem" word removed rather than replaced).

---

## P-section decisions (summary — full detail in plan file)

| P | Decision | Key action count |
|---|---|---|
| **P1 — production domain value** | Option A: commit `yourpublic.work` as default; production operator holds real value locally. | 4 site edits |
| **P2 — filesystem paths** | Symlink-powered: `~/projects/ESACP` (existing) covers ESACP; second symlink `~/projects/bespoke-apps → ~/projects/Logichem/` created at execute time. `BESPOKE_ROOT` env var with generic default for Python-code sites. `session_start.py:18` refactored to `__file__`-relative. `session_start.py:17` probes `$CLAUDE_PROJECT_DIR`, falls back to documented hardcoded memory-dir path. Runbook renames `LOGICHEM=` → `BESPOKE_ROOT=`. | 11 site edits |
| **P3 — virsh snapshot label** | `"ERPNext v13 Logichem DB Restored"` → `"ERPNext v13 Restored Baseline"`. No code string-matches the label, so no migration script needed. | 1 site edit |
| **P4 — labels / comments / docstrings** | Word deletion ("Restored Logichem ERPNext" → "Restored ERPNext"). UI label + Playwright test string coupled, must change together. | 5 site edits |
| **P5 — logo** | `git rm LogichemLogo.png` + `git add CompanyLogo.png` (content copied from `temp/ce_sri/development/testData/LogoDePrueba.png`). Binary replacement, not a rename. | 3 file operations + 1 code edit |

---

## Plan evolution during session

- **124 → ~203 count gap** surfaced at session start. User directed: don't reconcile; per-P-section enumeration is authoritative. Gap mostly reflects session-log growth while discussing the scrub.
- **Symlink contribution** (user pointed out `~/projects/ESACP -> ~/projects/Logichem/ESACP/` was already in place) eliminated the env-var complexity for ESACP itself. P2 design simplified accordingly.
- **Live `iridium.blue` dev-zone migration** was floated as an extension of P1's `yourpublic.work` adoption. Rejected as scope creep; filed as **#240** (depends on #239).
- **Additional P2 sites discovered during P4 discovery.** `toshy-fallback-install.sh:71,76`, `cesri_secrets.py:16,19`, `backup.py:10`, `ddl_views.py:11`, plus `erp_logichem_solutions` literal in ERPNextRestoreRunbook.md. Rolled into P2 without additional decision (same framework, same treatment).
- **Generic logo question.** User stated "we already have a generic logo" — traced through `provision_generic.py` and `logo.py`; discovered generic flow deploys **no** custom logo (ERPNext default stays). User resolved by directing copy of `LogoDePrueba.png` (sibling ce_sri repo, gitignored from ESACP) into the committed tree under `CompanyLogo.png`.

---

## Commit layout (recorded in plan)

Three commits, executed in order during the next session:

1. `fix(conduct): scrub client name from SUT strings` — P1 + P3 + P4 literals.
2. `refactor(paths): extract bespoke-app root to BESPOKE_ROOT env var + symlink convention` — P2.
3. `chore(branding): replace committed logo with generic placeholder` — P5.

---

## Carve-outs (intentional, documented)

- `platforms/kvm/session_start.py:17` retains hardcoded `-home-hasan-projects-Logichem-ESACP` memory-dir path as fallback when `$CLAUDE_PROJECT_DIR` is not provided by the CC harness. Load-bearing: CC session-dir name does not change retroactively.
- Production operator's local `hosts_map.yml:18` continues to hold `logichem.solutions` (one-line merge friction, accepted under P1 Option A; eliminated when #241 and #240 land in sequence).

---

## Issues — session record

| Ref | Action this session | State |
|---|---|---|
| **#239** | Plan complete. Comment posted: https://github.com/martinhbramwell/ESACP/issues/239#issuecomment-4276745501 | OPEN — execute session pending |
| **#240** (new) | Filed: live dev/staging zone migration `iridium.blue → yourpublic.work`. Depends on #239. | OPEN |
| **#241** (new) | Filed: `hosts_map.local.yml` overlay for operator-local overrides. Depends on #239. | OPEN |

No PRs opened. No PRs merged.

---

## Session-end audit — passed

Per global conduct rule + standard session-end protocol:

1. Promise / intent-phrase audit — executed; every commitment mapped to (a) executed command, (b) plan-file path, or (c) deferred-to-next-session note.
2. GH issues: all new findings posted as comments (#239) or captured at creation (#240, #241).
3. PRs: none opened — `mergedAt` check inapplicable.
4. Unresolved concerns at audit time: overlay-issue filing (resolved by filing #241); `$CLAUDE_PROJECT_DIR` verification (plan-resilient without); logo follow-up (resolved by user's copy direction).

---

## Deliverables

| Artifact | Path |
|---|---|
| Execution plan | `~/.claude/plans/conduct-scrub-client-name.md` (outside repo, on controller) |
| Session minutes | `docs/SessionLogs/2026-04-19-1622-session-minutes.md` (this file) |
| Next agenda | `docs/SessionLogs/2026-04-19-1622-next-agenda.md` |

---

## Branch state

- Branch `fix/conduct-scrub-client-name` at `4d7a8f8` at session start.
- Session commits: minutes + agenda (this commit). No SUT changes.
- `main` unchanged.
