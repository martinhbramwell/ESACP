# QA Verdict Log — `esacp-qa` Subagent (#341)

Records verdicts that turned out wrong, operator overrides, agent-failure-fallbacks, and trigger-skip incidents. **Not** every verdict — only the ones with signal.

**Batched at session-close** (one append per session alongside minutes). Bounded, predictable churn.

**Why this log exists:** if recurrence rate of bad verdicts or skipped invocations matches the original "3 regressions in ~36 hours" pattern that triggered #341, escalate to v2 hook-based enforcement (PreToolUse / PreCommit hooks firing automatically on `git commit` / `gh pr merge`). Until then, this log is the evidence base for that decision.

---

## Column legend

| Column | Meaning |
|---|---|
| **Date** | YYYY-MM-DD (session date, not entry date) |
| **Trigger** | Which trigger contract item (1=commit, 2=merge, 3=push, 4=destroy, 5=issue-close) |
| **Action** | Verbatim or summarised — `git commit -m "feat(qa): …"` etc. |
| **Verdict** | `approve` \| `approve-with-conditions` \| `reject` |
| **Outcome** | What actually happened: `proceeded`, `revised`, `overridden-by-operator`, `aborted`, `agent-unreachable-fail-open`, `agent-unreachable-fail-closed`, `verdict-skipped` |
| **Why-logged** | One line: false-positive, false-negative, override, skip, fallback, surprising-good-catch |
| **Notes** | Free text. Include reasoning excerpt or operator-override rationale. Link the commit hash / PR number where relevant. |

---

## Entries

| Date | Trigger | Action | Verdict | Outcome | Why-logged | Notes |
|---|---|---|---|---|---|---|
| 2026-05-03 | 1 | Session 5 — bootstrap commit `bcebe2d` (D1: agent file + `.gitignore` exception) | n/a | proceeded | bootstrap-exception | Per qa-contract §6 — agent file itself cannot be QA'd by an agent that does not yet exist. First commit *after* this routes through the agent. |
| 2026-05-03 | 1 | Session 5 — commit 2 staged (D2a + D2b + D4) attempted | agent-unreachable | aborted (deferred to Session 5.5) | fallback | First fail-closed event of the layer. `Agent type 'esacp-qa' not found` — root cause: in-session `/agents` UI on Claude Code 2.1.126 is read-only of the already-registered set, not a filesystem rescan. Full session restart via `./Cld.sh` required. Per qa-contract §5: trigger 1 fail-open allowed but a downstream push to main (hard-block, fail-closed) made operator-side fail-closed the right call for the whole arc. |
| 2026-05-03 | 1 | Session 5.5 Smoke #1 — `git commit -S` of D2a + D2b + D4 (`docs(qa): qa-contract + log seed for esacp-qa subagent (#341)`) | approve | proceeded → `3449a55` | first-verdict | First substantive verdict produced by the layer post-restart. Agent independently read all staged files, cross-checked agent file vs contract, verified relative-link correctness, scanned banned patterns + real names, and surfaced a fifth path (D4-as-stub) the parent missed — correctly rejected it as Path-C-with-extra-steps. Confirmed `docs(qa)` over `feat(qa)` because capability already shipped in `bcebe2d`. |
| 2026-05-03 | 2 | Session 5.5 Smoke #2 — `gh pr merge 342 --merge` to main | approve | proceeded → merge `3f107ef`; #341 auto-closed (`closedAt 2026-05-03T22:44:55Z`) | first-verdict + ruling | First merge verdict. **Notable ruling for future trigger-5 boundary cases**: agent decided the `fixes #341` PR-body auto-close is *subsumed* by this trigger-2 verdict — contract defines triggers by command (not effect); parent is not running `gh issue close`; the auto-close is a server-side consequence of the merge, not a separately executable parent operation; re-invoking after merge would be reactive (close already happened) and a separate `gh issue close 341` would be a no-op. No separate trigger-5 invocation required. |
| 2026-05-03 | 1, 3 | Session 5.5 routine approves: post-restart no-op ping; Smoke #1.5 session-log commit on main (`c6d132e`); `git push origin main` (trigger 3); `git push -u origin feat/esacp-qa-agent` (trigger 3, first-push with upstream tracking) | approve (×4) | proceeded | routine-batch | All trigger 1/3 with no surprise findings. Agent verified GPG signatures (good), divergence (1/0 fast-forward for both pushes), no pre-push hooks, no `.github/workflows/`, no branch protection rules. Smoke #1.5 used `git switch main` to commit Session 5 minutes + Session 5.5 agenda direct-to-main per session-log convention; agent confirmed direct-to-main matches 5/5 recent precedent. |

---

## Session-close batching protocol

At each session close (when filing minutes):

1. Review every `Agent(subagent_type: "esacp-qa", …)` invocation in the session.
2. Identify the ones with signal per the "Why-logged" column legend (skip routine approves with no surprise).
3. Append rows for each in this table.
4. If verdict count for the session is high enough that the table feels noisy, summarise: one row noting `N routine approves` + individual rows for everything notable.
5. Commit alongside session minutes (`docs(session-log)` scope is fine; no separate `docs(qa-log)` commit unless the log update is the only change).

---

## Cross-references

- Trigger contract: [`qa-contract.md`](qa-contract.md)
- Agent definition: [`../.claude/agents/esacp-qa.md`](../.claude/agents/esacp-qa.md)
- Issue: [#341](https://github.com/martinhbramwell/ESACP/issues/341)
- Originating memory rule: `feedback_enumerate_mechanisms_before_committing.md` (memory dir, not in repo)
