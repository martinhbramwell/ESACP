# QA Verdict Contract — `esacp-qa` Subagent (#341)

**Issue:** [#341 — feat(qa): esacp-qa subagent — pre-commit/merge/push verdict layer](https://github.com/martinhbramwell/ESACP/issues/341)
**Agent file:** [`.claude/agents/esacp-qa.md`](../.claude/agents/esacp-qa.md)
**False-positive / false-negative log:** [`internal_docs/qa-log.md`](qa-log.md)
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
| 2 | `git merge` or `gh pr merge` to `main` or any `umbrella/*` branch | **Hard-block by default; advisory when the §2.2 carve-out conditions all hold** | Parent stops; surface verdict to operator; operator decides override. |
| 3 | `git push` to remote | **Hard-block** | Parent stops; surface verdict to operator; operator decides override. |
| 4 | Destructive ops: `rm -rf`, `git reset --hard`, `git branch -D`, `gh pr close --delete-branch` | **Hard-block** | Parent stops; surface verdict to operator; operator decides override. |
| 5 | `gh issue close` (institutional-memory mutation) | **Hard-block** | Parent stops; surface verdict to operator; operator decides override. |

### 2.1 Combined T1+T3 invocation (codified de facto practice)

When a commit will be pushed in the same operational step — no intermediate inspection, no further edits, no waiting for an intervening operator decision — the parent invokes a **single combined T1+T3 verdict** on the commit-and-push pair. The verdict covers both gates; no separate T3 invocation is needed.

Appropriate when all of the following hold:

1. The push immediately follows the commit (no intermediate state to re-verdict).
2. The push target is one of: a feature branch; `main` on a project where main is the only branch (e.g., LogiSoluMemory, BaRe); or `main` on a project where the operating convention explicitly permits direct-to-main for the commit's category (e.g., ESACP doc-only session-close commits per the S30–S36 precedent — feature work on ESACP still goes through feature-branch + PR + T2).
3. No new commits will be added between the verdict and the push.

If any condition fails, T1 and T3 are invoked separately.

The invocation prompt is labeled `Trigger 1+3 (combined pre-commit + pre-push)` and includes both the staged diff (T1 input) and the push target (T3 input). The verdict trailer carries `hard_block: true` (inheriting the T3 hard-block scope; T1's advisory scope is subsumed). On `reject`, the parent does not commit; on `approve-with-conditions`, the parent addresses conditions before commit.

Codified from S33+ practice. Pre-S33 rows in `internal_docs/qa-log.md` show the historical separate-invocation pattern.

### 2.2 T2 advisory carve-out

T2 (merge) is hard-block by default. It downgrades to **advisory** when all three of the following conditions hold:

1. The PR head commit (or commit chain) already received an `approve` (or `approve-with-conditions` with conditions addressed) **combined T1+T3 verdict** on the source branch.
2. No additional commits have been added to the source branch since that verdict.
3. The merge is a clean fast-forward or squash, and no rebase, cherry-pick, or amend of any kind has been performed on the source-branch commits since the prior T1+T3 verdict. Bit-identical content after a rebase does **not** satisfy this condition — the rule is categorical on the operation, not on its output.

When all three hold, the parent confirms the conditions explicitly in its T2 invocation prompt (cite the prior verdict's invocation ID) and proceeds with advisory verdict. If any condition fails, T2 reverts to hard-block.

**Carve-out rationale**: Sessions 5.5–36 catch-rate data (109 verdicts) shows T2 combined `approve-with-conditions` + `reject` rate is 17%, and inspection of those rows shows most T2 catches verify what T1+T3 already caught on the same commits. Full rollup in [#380](https://github.com/martinhbramwell/ESACP/issues/380). The carve-out preserves the catch surface for merges that bypassed prior QA (manual cherry-picks, multi-source merges, rebased branches) while eliminating duplicate verdicts on already-QA'd content.

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

Both failure-mode paths must also append a row to `internal_docs/qa-log.md` at session-close batching.

**"Malformed verdict" defined narrowly** (clarification per #367): a verdict whose substantive answer (`approve` / `approve-with-conditions` / `reject`) is unclear or self-contradictory. Flag inconsistencies on an unambiguous verdict — e.g. `hard_block: false` on an `approve` verdict for a Trigger 2–5 action — are NOT malformed for fail-closed purposes. The parent reads the substantive answer and proceeds. The `hard_block` flag determines override semantics on `reject` only; on `approve`, the flag has no operational effect. Note such inconsistencies once in `internal_docs/qa-log.md` if useful, but do not treat them as fail-closed events and do not build escalation watches around them in isolation.

---

## 6. Bootstrap exception

The first commits that create the agent itself cannot be QA'd by an agent that doesn't yet exist. Specifically the bootstrap commits in branch `feat/esacp-qa-agent` (#341 implementation):

- D1 — `.claude/agents/esacp-qa.md` (the agent file itself)
- D2a — `internal_docs/qa-contract.md` (this document)
- D2b — `CLAUDE.md` pointer line
- D3 — memory cross-ref update in `feedback_enumerate_mechanisms_before_committing.md`
- D4 — `internal_docs/qa-log.md` log seed

These proceed under self-enforced rules + plan-locked design (`~/.claude/plans/esacp-qa-agent.md`). The first commit *after* the agent file lands on the branch routes through the agent — that is the first smoke test (#341 acceptance #3).

After the agent file is committed, the parent must reload subagents (`/agents` in the CLI, or session restart) before the agent is reachable. The plan §4.5 sequencing accommodates this.

---

## 7. False-positive / false-negative log

`internal_docs/qa-log.md` records verdicts that turned out to be wrong (false positives = unnecessarily rejected; false negatives = approved when it shouldn't have been) and operator overrides. Batched at session-close (one append per session alongside minutes), bounded and predictable churn.

Log row template lives in `internal_docs/qa-log.md` itself. Goal: surface skip incidents and verdict-quality drift; if recurrence rate matches the original "3 regressions in 36 hours" pattern that triggered #341, escalate to v2 hook-based enforcement.

### 7.1 Rolling-window recalibration audit

At each Session-25 boundary — where session-count is read from the ESACP session-log rows in `internal_docs/qa-log.md` only, not summed across other-bucket sessions — the parent runs a rolling-window analysis on the **most-recent 50 ESACP qa-log rows**. For each trigger type, compute the combined `approve-with-conditions` + `reject` rate. If that rate falls below **10%** for any trigger, surface the finding to the operator with a contract-revision recommendation (further carve-out, downgrade to advisory, or retirement).

The audit is **detection-only**: surfacing does not auto-mutate the contract. The parent files an issue + recommendation; the operator decides whether to revise.

Rationale: catches-per-invocation is the load-bearing signal. Sessions 5.5–36 showed 4-5 of 6 rejects concentrated in Sessions 5.5–10 (early-calibration phase); recent rate has dropped sharply. A periodic check ensures the contract revises down as the parent's internalisation of rules makes specific triggers redundant — rather than letting "approve" pile up indefinitely on rubber-stamped lanes.

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

## 9.5 Branch-base currency check (#673)

Before any T1 (commit) or T2 (merge) verdict, the agent runs
`./tools/branch_currency.py --no-fetch` (strictly read-only `git rev-list`
against the already-fetched `origin/main`; the parent owns the fetch) and
hard-blocks a merge whose source branch — especially any `umbrella/*` — is
behind `origin/main` without an explicit rebase intent in the parent's
deliberation. This is the action-time enforcement of the rebase-cadence rule;
`sync_check.sh` §19 is the complementary session-start surfacing. Root cause:
S116 cut a sub-branch off an umbrella 30 commits stale and only found out live.

## 9.6 Anti-deflection check (#675)

The parent has a demonstrated reflex (S116) to launder sole-actor agency into
agentless, passive-causal grammar ("the plan didn't foresee", "nobody
reconciled", "bit-rot") and to assert system-state facts without citing the
evidence — corroding the trust channel that is the platform's core promise.
Self-policing failed; the independent layer (this agent) is the guardrail. On
every T1/T2 verdict the agent examines the commit message, PR body, and the
parent's deliberation for (1) agentless framing of sole-actor state — using
`./tools/deflection_lint.py` (a conservative seed denylist) as a pre-filter,
then judgment beyond it — and (2) state-claims lacking a cited command output.
Deflection in the action's own artifacts → approve-with-conditions (rewrite to
own the agency / cite the evidence); deflection in the deliberation → flagged in
reasoning. Not a hard_block on its own. Novel deflections the agent catches feed
back into `deflection_lint.py` — judgment grows the mechanical layer.

## 10. Revision history

| Date | Change | Source |
|---|---|---|
| 2026-05-03 | v1 initial — implementation of #341 | `feat/esacp-qa-agent` branch, D2a |
| 2026-05-12 | v2 — risk-tiered triggers calibrated on Sessions 5.5–36 data (109 verdicts): T2 advisory carve-out when prior T1+T3 approve already covers the commits; T1+T3 combined invocation codified; rolling-window recalibration audit at every 25th ESACP session | [#380](https://github.com/martinhbramwell/ESACP/issues/380) |
| 2026-05-12 | v2.1 — §2.1 condition 2 broadened to recognise repo-specific direct-to-main conventions (e.g., ESACP doc-only session-close commits per S30–S36 precedent), so the §2.1 carve-out covers the very lane that motivated it. v2 wording was under-inclusive and caught by the v1 QA agent on the Session 37 session-close commit. | [#382](https://github.com/martinhbramwell/ESACP/issues/382) |
| 2026-06-08 | v2.2 — §9.5 branch-base currency check: agent runs `tools/branch_currency.py` and hard-blocks a merge on a base behind origin/main (esp. `umbrella/*`). Action-time teeth for the rebase-cadence rule; pairs with `sync_check.sh` §19. | [#673](https://github.com/martinhbramwell/ESACP/issues/673) |
| 2026-06-08 | v2.3 — §9.6 anti-deflection check: agent flags agentless/passive-causal framing of sole-actor state + unevidenced state-claims in commit message / PR body / deliberation, using `tools/deflection_lint.py` as a seed pre-filter. Independent guardrail on the parent's self-reporting register. | [#675](https://github.com/martinhbramwell/ESACP/issues/675) |
