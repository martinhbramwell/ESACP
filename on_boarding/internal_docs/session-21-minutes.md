# Session 21 minutes — 2026-06-19

**Branch:** `on_boarding` (Junior). **Started as:** S21 agenda
([#723](https://github.com/martinhbramwell/ESACP/issues/723)) — confirm transparent-router
robustness, persona validation, downstream transparency pass. **Became:** an
operator-driven redesign of the entire onboarding flow — the **Letter-of-Introduction
model** — captured as **U0** in
[`letter-of-introduction-model.md`](letter-of-introduction-model.md)
([#727](https://github.com/martinhbramwell/ESACP/issues/727) / PR
[#728](https://github.com/martinhbramwell/ESACP/pull/728)).

## The arc
The #723 plan was never run. A question about whether the Kit/Skill files had lost
content (they hadn't — they're test canaries, single commit `0996a34`) opened into a
full re-examination of the onboarding architecture, and the operator drove a redesign
across ~a dozen turns. **The complete design lives in the U0 doc**; these minutes record
only what happened and where the decisions are durably homed.

## ESSENTIAL KNOWLEDGE — carry forward
All in [`letter-of-introduction-model.md`](letter-of-introduction-model.md); headlines
(full rationale in the doc sections cited):

1. **Free claude.ai is openly Claude, drafting a letter of introduction to Nick** — who
   lives behind the door in Claude Code. Supersedes "you are Nick" (the alignment-refusal
   root cause). [§0–§2]
2. **The ~$20 is Claude Pro, which INCLUDES Claude Code** (verified live, sources in §3).
   One subscription, not two costs. The power-up is Claude Code, not "Pro-Nick."
3. **Account-state blindness** — the chat can't see plan/billing/usage or infer tier from
   its model; every plan-dependent step is visitor-confirmed. [§4]
4. **Two-letter / three-doc rail** (`first_visit → setup_guide → install_planner`): at
   each boundary the upstream Claude writes a letter, the human pastes it downstream. [§6, §9]
5. **The gate** (load deep `setup_guide.md` before install help): no hard guarantee on the
   platform → human-pasted trigger (Letter 1) + anti-confabulation + letter-as-receipt +
   canary. [§7]
6. **8-rung string→crate ladder**; chain→winch = human-letters→machine-automation; we own
   rungs 1–4 + Letter 2, rungs 5–8 are the existing platform. [§10]
7. **Informed consent before the paywall** — TIME is the primary axis, not money; the
   "reckoning" gh-pages section + two-question self-check; warm off-ramp; deferred
   walkthrough video. [§11]

## Process notes
- **#723 kept OPEN as the umbrella** for the U1–U8 build plan (operator decision);
  per-unit issues filed as units are tackled.
- esacp-qa T2 on the U0 merge (PR #728) = `approve`; doc-only, Junior-territory.
- GPG pinentry cancelled once on the #727 commit → operator tty-unlock
  (`feedback_gh_signing_pinentry_timeout`), retried clean.
- Cost facts verified via the claude-api skill + WebSearch/WebFetch, not memory
  (`feedback_verify_usage_mechanics`). The standing memory
  `project_claudeai_free_connector_capability` phrases the cost loosely ("Claude Code is
  the one unavoidable cost"); design doc §3 is now authoritative — optional memory
  refinement offered, not done.

## State at close
| | |
|---|---|
| **U0 (design capture)** | ✅ done — `letter-of-introduction-model.md`; #727 closed; PR #728 merged |
| **[#723](https://github.com/martinhbramwell/ESACP/issues/723)** | OPEN — umbrella for U1–U8 |
| **Next (U1)** | `index.md` cost fix + the "reckoning" section |
| **#715/#717/#719** | still OPEN — robustness close folded into U6 |
| **Deferred** | walkthrough video (U8, post-beta) |

Design detail: [`letter-of-introduction-model.md`](letter-of-introduction-model.md).
