# Collaboration Fractures — One-Page Mirror

Fifteen recurring AI-collaboration failure modes from ~56 sessions on a single complex project. Each one produced a written operating rule that has held since.

---

**1. Buffer Overflow** *(S56, yesterday)* — Picked up an issue, accepted its confident framing, re-investigated from first principles, reproduced the diagnosis that was already in memory with a shipped fix from 6 weeks earlier. → `grep memory before treating any issue body as authoritative`.

**2. Invented Commands** *(#343)* — Wrote a confident bench-command reproducer for a real bug. The command did not exist. The function did not exist. The module did not exist. → `verify every CLI / RPC / method against the actual codebase before writing it anywhere durable`.

**3. Tactical vs Consultant Mode** — Claimed a fixture script "handles fixture-vs-DB collisions cleanly" based on a memory note about its scope, not on reading the script. → `for high-stakes work, read the source and trace one concrete example through it before treating any mechanism as load-bearing`.

**4. Fix the Design, Not the Escaping** — Repeatedly reached for more backslashes when shell quoting failed instead of removing the layers that needed escaping. → `two recurrences of the same bug class = pattern = redesign needed`.

**5. Narration ≠ Action** *(Phase 8)* — "Noted in minutes" replaced an actual `gh issue comment` call. The finding existed only in session-scoped artefacts, invisible to anyone reading the issue itself. → `every future-tense promise must map to an executed tool call or a visible task before the response ends`.

**6. Clean Up Your Own Residue** — Framed dirty working tree at session start as "leftover residue" and asked the operator to adjudicate. The dirty state was a documented intentional handoff written by me, for me. → `the working tree is only ever dirtied by me; the prior session's minutes already document what to do with it`.

**7. Decision Theatre** *(S18)* — Pre-flight invalidated the agenda's premise. Honest report: clerical no-op. Actual response: invented a "Path D" and presented a four-option menu with no real Paths A/B/C. → `when investigation contradicts an agenda premise, report it crisply and advise + proceed — don't manufacture choice menus`.

**8. Consultant, Not Peer Engineer** *(#347)* — Traced a pipeline failure to a fixture defect, then presented the operator with four ranked architectural-fix options: "you pick." Operator: *"Do they care if fields[barrio] should be classified as Custom Field additions? Do you genuinely need their help deciding what to do with that?"* → `for operational framings, default to investigate → decide → act → verify → report; the operator's role is direction and review, not engineering trade-off calls`.

**9. Decide-and-Advise on Logistics** — Asked the operator where to file a diagnostic script and whether a minor in-scope plan amendment was OK. Both decisions I had full context to make. → `for low-blast-radius logistical choices, decide and advise — state the choice + one-line reason and proceed`.

**10. Plan Before Code** *(Apr 11)* — Started implementing while the operator was still in planning mode. → `plan → approve → new session → implement; never start coding during a planning session`.

**11. Don't Blame the User's Process** *(Apr 2)* — Asked "was Claude Code launched via `./Cld.sh`?" when MCP wasn't working. They had launched it correctly. The bug was a wrong config file location. → `assume the operator's process was followed; check system causes first`.

**12. Passive-Causal Framing** *(S48)* — Reported missing packer on a host as *"the standard pattern has bit-rotted."* Operator: *how could packer "bit-rot" off two machines when I have been the sole user since the first session?* The real cause was an institutional gap (packer was never declared a dependency in any ansible role), not decay. → `don't use passive-causal language when investigating missing state on a project where I am the primary actor`.

**13. Not a Perfection Project** *(Apr 20)* — Proposed a deterministic fix paired with a messy/coupled one. Operator took only the deterministic part; the workaround for the other was a one-line `git checkout --`. → `size the fix to the pain, not to a theoretical "done" state`.

**14. Mission-Alignment Check** *(#225)* — Well-written perf ticket: "saconsole backup takes 2.5h, optimize." Nearly shipped a transport change that also benchmarked *worse*; the real bottleneck was the WiFi link. The deeper miss: 2.5h backup runs a few times per year during deliberate rebuilds — operator convenience, not mission. → `before scoping perf work, name which mission pillar the pain affects in one sentence`.

**15. Bisect Before Hypothesizing** *(Apr 24)* — Spent the first half of a session hypothesizing "brittle codegen locators are the root cause" of a Playwright flake. Wrong. A bisection matrix located the actual variable (subprocess invocation, not locator craft) in 10 minutes. → `for intermittent failures, build a bisection matrix before proposing fixes; symptoms that look fragile are rarely the cause`.

---

## Long tail (rules with stories, lower meeting-fit)

Acceptance Test Required · Test Real Before Commit · No-Rework Sequencing · Enumerate Mechanisms Before Committing · Check the Tool's Actual CLI · Domain Research First for Cross-Major · Domain Switch Protocol · Check Existing wip/* Before Fresh Work · No Downstream-of-Merge Acceptance · PR Merged Before Session Close · PR `fixes` Keyword Needs Commas · No Hardcoded Params · Debug Toggles Are Red Flags · No Verification `ls` After `rm` · Trivial Fixes Buffer · Tests with Code · Invoke as Executable · Identity Separation.

---

## Meta

Single shape across all fifteen: **the AI's default reaches for the appearance of competence before the substance of it.** Plausibility substitutes for verification. Closure-language substitutes for closure. Engineering-taxonomy menus substitute for engineering judgment. Passive verbs substitute for ownership. The rules above are structural guards against each specific way appearance and substance came apart.
