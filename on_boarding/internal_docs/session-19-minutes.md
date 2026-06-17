# Session 19 — Minutes: Mode-A router redesign

**Dates:** 2026-06-16 → 2026-06-17 · **Branch:** `on_boarding` · operator-driven, very long.

This session **diverged from its agenda** (#647 Candidates A/B) when the operator
brought a v4 `first_dialog.md` rewrite from another machine. That opened a full
redesign of the Mode-A "Nick" persona, driven by repeated live mode-2 tests on a
free-tier claude.ai account.

## Outcome in one line
The **goal-staged router** works: a free-tier visitor's Claude, given **no final goal**
during intake, conversationally extracts three values (Type / Skill / Kit), fetches the
matching Type page, and only **then** receives its goal — curing the install-planning
reversion that broke every prior version. **Validated once; reproducibility pending** (S20, #712).

---

## ESSENTIAL KNOWLEDGE — carry forward

1. **Goal-staging is THE fix for the install-planning reversion.** The model's default
   "helpful technical assistant" reflex hijacks any final goal it's given up front — so a
   technical visitor's reply (e.g. "V13→V16 upgrade") triggered install-planning in every
   goal-up-front version. Withholding the goal during intake leaves the reflex nothing to
   latch onto. **Structural fix (hide the goal until after dispatch), not stronger wording.**
2. **Multi-stage fetch works.** A free-tier model *will* fetch a URL that appears only inside
   an already-fetched doc (the provenance rule's sanctioned "fetch the result link") and
   returns its real content — proven cleanly by `stage_test.md` (#707) and then in the real
   goal-staged run. Earlier dispatch-skips were persona complexity + rich content drowning
   the directive, NOT an inability to fetch.
3. **Free-plan claude.ai fetch constraints** (memory `project_claudeai_free_fetch_constraints`):
   provenance rule (model can't fetch a URL it constructs/never saw); query-string changes
   don't bust the cache; POST blocked; **redeploy-to-same-path serves STALE cross-conversation**
   → bump the filename every publication (`first_visit_NNN.md`). Cache scope (per-account vs
   global) and TTL still unknown.
4. **Critical behaviour must be singular and prominent.** Buried instructions get ignored; the
   model won't dispatch when persona + rich content compete. Make the immediate task the only
   thing in view.
5. **The working architecture:** goal-staged router (`first_visit_002.md`, intake-only, no goal)
   → 3 goal-revealing Type pages (`visitor/{curious,owner_general,owner_specific}.md`). **Skill
   and Kit are delivery modifiers carried into the one Type page, NOT separate fetches.** Type
   is **provisional** — "Type can change — re-dispatch freely" (a curious visitor may warm up).
6. **The live front door is still v4 `first_dialog.md`** — unchanged all session. `first_visit_002.md`
   is the validated staging successor, awaiting reproducibility + a promotion decision.

---

## FAILED EXPERIMENTS / DEAD ENDS — do not repeat

1. **Dynamic param-driven endpoint** (rotating subdomains / query strings to pass visitor state):
   dead — provenance blocks model-constructed URLs, the cache ignores the query string, POST is
   blocked, and it leaks the visitor's data into proxy/server logs. Dynamic per-request state
   must use an **MCP connector (tool call)**, not HTTP fetch/POST.
2. **Multi-file router with the goal given up front** (`first_visit.md` multi-file; `first_visit_001.md`):
   caused the install-planning reversion. Superseded by goal-staging — **#705/#706 closed.**
3. **16-file Skill×Kit matrix as separately-fetched pages:** unnecessary. Skill/Kit are delivery
   modifiers carried into one Type page, not pages to fetch.
4. **Menu / multiple-choice classification:** rejected by the operator (an indignity to visitors).
   Goal-staging made it unnecessary — conversational extraction of the three values works.
5. **§3T snitch instrumentation as a permanent feature:** it was a *diagnostic scaffold* to prove
   fetch + cache-defeat (#703), and it did its job. Removed from the goal-staged handlers.
   `stage_test.md` remains as a reusable isolation probe.

---

## Process notes
- ~6 full 1:1:1 cycles + closeout, every trigger QA'd (T1/T3/T2/T5; T2 advisory per
  `project_on_boarding_trunk_vs_default`). GPG pinentry timed out ~3× → operator tty-unlock
  (`feedback_gh_signing_pinentry_timeout`).
- The egress cache poisoned `first_visit.md` once (4 fetch retries) → filename bump.
- One accidental wrong-base branch (`test/707` cut off `fix/705`) was caught by esacp-qa at T2
  and fixed with a clean cherry-pick rebuild — discipline working as intended.

## State at close
| | |
|---|---|
| **LIVE front door** | `first_dialog.md` = v4 (unchanged) |
| **STAGING (validated once)** | `first_visit_002.md` + 3 goal-revealing Type pages |
| **STAGING (clutter, cleanup #710)** | old `first_visit.md`, `stage_test.md`, `skill_/kit_*` stubs |
| **Open issues** | #712 (S20 agenda), #710 (cleanup), #511/#448 (deferred) |

Design detail: [`mode-a-router-design.md`](mode-a-router-design.md).
