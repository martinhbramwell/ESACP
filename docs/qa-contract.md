# QA Verdict Contract — `esacp-qa` Subagent (#341)

**Issue:** [#341 — feat(qa): esacp-qa subagent — pre-commit/merge/push verdict layer](https://github.com/martinhbramwell/ESACP/issues/341)
**Agent file:** [`.claude/agents/esacp-qa.md`](../.claude/agents/esacp-qa.md)
**False-positive / false-negative log:** [`docs/qa-log.md`](qa-log.md)
**Memory rule the agent enforces structurally:** [`feedback_enumerate_mechanisms_before_committing.md`](../../.claude/projects/-home-hasan-projects-Logichem-ESACP/memory/feedback_enumerate_mechanisms_before_committing.md) *(memory-dir path; not in repo)*

This document is the **single source of truth** for the trigger contract. CLAUDE.md carries a one-line pointer here. The plan file `~/.claude/plans/esacp-qa-agent.md` is implementation history; this doc supersedes it for live operation.

---

## 1. What the agent is

A project-scoped Claude Code subagent that the parent agent (Claude Code, working with the operator) invokes **explicitly** before performing any of the trigger operations below. The subagent reads the rules, reads the action, reads the parent's deliberation, and returns a structured verdict. The agent never mutates state; its output is a verdict block.

Independent judgment, not checklist-running. A skill or hook executed by the parent would inherit the parent's blindspots; an agent invoked via `Agent(subagent_type: "esacp-qa", …)` runs in a fresh context with its own reading of the rules.

---

## 2. Trigger contract — when the parent must invoke the agent

The parent must obtain a verdict before any of these operations are executed. Verdict scope per trigger:

| # | Operation | Scope | Reject behaviour |
|---|---|---|---|
| 1 | `git commit` (any branch) | **Advisory** | Parent revises; if parent genuinely disagrees after attempting revision, parent documents the override in its response and proceeds. |
| 2 | `git merge` or `gh pr merge` to `main` or any `umbrella/*` branch | **Hard-block** | Parent stops; surface verdict to operator; operator decides override. |
| 3 | `git push` to remote | **Hard-block** | Parent stops; surface verdict to operator; operator decides override. |
| 4 | Destructive ops: `rm -rf`, `git reset --hard`, `git branch -D`, `gh pr close --delete-branch` | **Hard-block** | Parent stops; surface verdict to operator; operator decides override. |
| 5 | `gh issue close` (institutional-memory mutation) | **Hard-block** | Parent stops; surface verdict to operator; operator decides override. |

**Not in scope for v1** (parent does not need a verdict, but may invoke voluntarily for sanity-check):

- Merge to a feature branch (sub-branch of `umbrella/*`, or non-main feature branches generally)
- Branch creation
- Tag creation
- `gh issue create` / `gh issue comment` (writes to issues but not destructive of memory)
- `gh pr create` / `gh pr comment` / `gh pr review` (PR opening/discussion is not the merge gate)
- Local file edits / writes — judgment lives at the commit boundary, not per-edit

**Future v2 candidates** (parked, not in v1):
- PreToolUse / PreCommit hooks firing automatically on `git commit` / `gh pr merge` (defer until/unless invocation pattern is skipped in practice)
- Auto-skip on `--dry-run` invocations
- Per-branch policy variation (umbrella vs main vs feature)

---

## 3. What the parent supplies in the invocation prompt

The parent's `Agent(subagent_type: "esacp-qa", prompt: …)` invocation must include:

1. **Planned action** — verbatim command (e.g. `git commit -m "..."`, `gh pr merge 341 --squash`, `git push origin feat/foo`, `rm -rf /path`).
2. **Diff or PR metadata** —
   - For commits: `git diff --stat` + full `git diff` against the previous commit (or `--staged` if pre-commit).
   - For merges: `gh pr view <n>` + `gh pr diff <n>`, plus the target branch.
   - For destructive ops: the command and the target paths/refs; ideally `git status` + `git log --oneline -5` for context.
   - For `gh issue close`: the issue body + the closing commit hash.
3. **Considered paths + chosen path + why** — the parent's enumeration of mechanisms it weighed, which it picked, and the reasoning. This is the load-bearing input for the anti-rubber-stamp evaluation (`feedback_enumerate_mechanisms_before_committing.md`).
4. **Mission-lens / reversibility framing** — whether the action serves the mission, whether it is reversible, blast radius.

**Missing or thin input is itself a verdict signal.** A bare "please approve this commit" with no diff and no deliberation should usually be rejected (advisory) or hard-blocked, with reasoning that requests the missing context.

---

## 4. Verdict transport — structured trailer

The agent's reply ends with a fenced block:

```
ESACP-QA-VERDICT:
  status: approve | approve-with-conditions | reject
  conditions: [<list of revisions required, omit field if status != approve-with-conditions>]
  reasoning: <one-paragraph why, ≤ 80 words>
  hard_block: true | false
```

`hard_block: true` is set when the action is in the hard-block subset (triggers 2–5). Caller parses the block; everything before it is freeform reasoning the operator may read.

JSON-only response was considered and rejected: the agent's judgment is the load-bearing output, and JSON-only would obscure reasoning during smoke-tests. Trailer-block keeps reasoning visible and verdict mechanically parseable.

---

## 5. Failure-of-agent fallback

Two failure modes:

| Failure | Hard-block triggers (2–5) | Advisory trigger (1, commits) |
|---|---|---|
| Agent invocation errors (tool unavailable, schema mismatch) | **Fail-closed** — do not proceed; surface error to operator; stop. | **Fail-open with mandatory note** — proceed but log "agent unreachable" in the parent's response so operator sees the gap. |
| Agent returns malformed verdict (no trailer block, contradictory fields) | **Fail-closed** — same as invocation error. | **Fail-open with mandatory note** — same as invocation error. |

Both failure-mode paths must also append a row to `docs/qa-log.md` at session-close batching.

**"Malformed verdict" defined narrowly** (clarification per #367): a verdict whose substantive answer (`approve` / `approve-with-conditions` / `reject`) is unclear or self-contradictory. Flag inconsistencies on an unambiguous verdict — e.g. `hard_block: false` on an `approve` verdict for a Trigger 2–5 action — are NOT malformed for fail-closed purposes. The parent reads the substantive answer and proceeds. The `hard_block` flag determines override semantics on `reject` only; on `approve`, the flag has no operational effect. Note such inconsistencies once in `docs/qa-log.md` if useful, but do not treat them as fail-closed events and do not build escalation watches around them in isolation.

---

## 6. Bootstrap exception

The first commits that create the agent itself cannot be QA'd by an agent that doesn't yet exist. Specifically the bootstrap commits in branch `feat/esacp-qa-agent` (#341 implementation):

- D1 — `.claude/agents/esacp-qa.md` (the agent file itself)
- D2a — `docs/qa-contract.md` (this document)
- D2b — `CLAUDE.md` pointer line
- D3 — memory cross-ref update in `feedback_enumerate_mechanisms_before_committing.md`
- D4 — `docs/qa-log.md` log seed

These proceed under self-enforced rules + plan-locked design (`~/.claude/plans/esacp-qa-agent.md`). The first commit *after* the agent file lands on the branch routes through the agent — that is the first smoke test (#341 acceptance #3).

After the agent file is committed, the parent must reload subagents (`/agents` in the CLI, or session restart) before the agent is reachable. The plan §4.5 sequencing accommodates this.

---

## 7. False-positive / false-negative log

`docs/qa-log.md` records verdicts that turned out to be wrong (false positives = unnecessarily rejected; false negatives = approved when it shouldn't have been) and operator overrides. Batched at session-close (one append per session alongside minutes), bounded and predictable churn.

Log row template lives in `docs/qa-log.md` itself. Goal: surface skip incidents and verdict-quality drift; if recurrence rate matches the original "3 regressions in 36 hours" pattern that triggered #341, escalate to v2 hook-based enforcement.

---

## 8. Anti-rubber-stamp principle

The agent's purpose is **independent judgment**. The parent's deliberation in the invocation prompt is input, not authority. The agent specifically evaluates:

- Did the parent list 2+ paths, or did it state one and post-rationalise?
- Was the rejected option a strawman or a real alternative?
- Does the chosen path actually address the goal, or a related-but-easier problem?
- Are the considered tradeoffs the load-bearing ones?
- Is there a third path the parent did not consider that the rules surface?

If any red-flag, raise it in reasoning and adjust the verdict. A reject + "your enumeration looked thin; did you consider X?" is more useful than a rubber-stamp approve.

---

## 9. Tool-grant boundary

The agent has `Read, Bash, Grep, Glob`. **`Bash` is whole-or-nothing** — the CLI does not enforce read-only. The agent self-enforces via its system prompt (`.claude/agents/esacp-qa.md` §"Tool-use boundary"):

- Allowed: `git diff/log/status/show`, `gh pr view/diff/list`, `gh issue view/list`, `ls`, `cat`, `wc`, `head`, `tail`, `grep`, `find` (read-only), etc.
- Forbidden: any mutating git/gh command, `rm`, `mv`, `cp` into repo, `chmod`, `chown`, `sudo`, file redirections, package install/remove, service management, mutating SSH/ansible/virsh/docker calls.

If the agent ever wants to run a forbidden command, that is itself verdict-relevant (input is missing context, or agent is slipping into doer-mode). It notes this in reasoning and continues read-only investigation.

This is acceptable for v1 because the agent's output is text (a verdict), not actions. An agent that runs a write command would itself be evidence the verdict layer is broken.

---

## 10. Revision history

| Date | Change | Source |
|---|---|---|
| 2026-05-03 | v1 initial — implementation of #341 | `feat/esacp-qa-agent` branch, D2a |
