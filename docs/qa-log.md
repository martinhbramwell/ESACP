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
| YYYY-MM-DD | N | `<verbatim cmd>` | approve\|approve-with-conditions\|reject | proceeded\|revised\|overridden-by-operator\|aborted\|... | false-pos\|false-neg\|override\|skip\|fallback\|good-catch | (template — delete on first real entry) |

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
