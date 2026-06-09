# 2026-06-09 1207 — Session 117 minutes

> Objective (pinned at start): **a bounded discussion → decision-record on the guardrail-forkability
> defect #683 and the Beaverdam-org overhaul #682 — advance both to a DECIDED state; do NOT execute.**
> Achieved, plus one operator idea folded in (concurrent "Linus" agent, #686).

## Class
**Discussion / decision-record.** No code PRs; deliverables are consolidated issue bodies (#682/#683),
one new issue (#686), and two memory files + index pointers. **Not an introspection-sidebar** despite
two MEMORY.md index *appends* — following the S116 precedent, incidental index appends accompanying the
session's primary work are not an indexing *restructuring* and not carry-forward attrition. One issue
filed (#686).

## What happened

### Decided #682 (Beaverdam-org overhaul) — full decision-record
- **Extraction model — two layers.** Big-bang "read everything, migrate all generic code" audit
  **rejected** (perfection trap: ~24k LOC + 138 memory files + 500 SessionLogs, ~95% correctly
  tenant-specific). Replaced by (1) **planned subsystem extraction** for standing infrastructure —
  the repo's directory structure already names the ~dozen subsystems, collapsing ~660 per-file rulings
  to ~12 per-subsystem ones — and (2) **capture-forward** for discipline/learning + ongoing deltas
  (per-PR contributor-Skill ruling).
- **Subsystem dispositions (first-pass)** recorded: observability=extract-whole; cytoscape=extract-viewer;
  template-build=scrubbed-skeleton (Wyatt rules the seam); pipeline=framework-only; ansible=scrubbed-roles
  (Paco); BaRe=promote-as-is. ≈6 subsystems ⇒ seed + ~5–7 scoped sessions, each shipping value.
- **Sub-decisions:** repo topology = extract new upstream, ESACP keeps its name + becomes the LogiSolu
  fork (squares with #541/#533 — no rename); umbrella = the **GitHub org**, independent repos, **NOT
  submodules** (they sabotage forks); Skills propose / operator+Linus create repos (#358 sprawl guard);
  upstreaming gate = #614-generalized denylist grep (floor) + contributor-Skill judgment (ceiling);
  phasing = **MVP** (org + 1 upstream + fork + 2 thin Skills + one round-trip); consolidation — #615→Linus
  coordinator Skill, #536/#656/#662 relate-but-distinct.

### Decided #683 (guardrail-forkability defect)
Fix homed in the #682 seed: a `CHARTER.md` in the upstream states the three guardrails as **universal
trustworthiness invariants** (detect own state divergence; verify plan vs live system before acting;
report own actions without laundering agency); §9.6 + docstrings de-specified to cite the universal
failure mode; S116 story demoted to a one-line changelog example.

### Folded in: concurrent "Linus" agent (#686) + deferral revision
Operator proposal: boot Linus as a **concurrent independent agent** on Mighty (read-only over the
workspaces) building the Beaverdam org/repos in parallel with Senior (V15/V16) and Junior (on-boarding).
Verdict: not absurd — concurrency dissolves the constraint that forced the deferral (the deferral was
about not starving the object-level work of *attention*, not about risk). **Deferral revised:**
attention-competing extraction stays deferred until V15-ready; concurrent independent extraction of
**stable** subsystems by Linus may start now — scoped to stable/generic subsystems only (leave the
actively-churning template-build + pipeline until V16 settles), read-broad/write-scrubbed, no age key,
`gh` scoped to the Beaverdam org. Doubles as the proof-of-thesis for autonomous bounded-domain ownership
(success signal = how often Linus needed the operator). **Not started in S117** — own scoped unit.

### Partnership reorientation (memory)
Operator named, and I owned, that I had been operating at the wrong altitude — leading with mechanism/
housekeeping when the work was at mission altitude. Captured as `feedback_operate_at_mission_altitude.md`
and `project_beaverdam_mission_and_concurrent_personas.md` (the SME-resilience *why*).

### #460 residue cleanup (incidental)
The LogiSoluMemory working tree carried **uncommitted S116 residue** (`feedback_no_passive_causal_framing.md`
mod + `project_session_integrity_guardrails.md` untracked) — the exact cross-repo-residue failure #460
warns of (S116 committed its ESACP tree but left the memory repo dirty). Committed alongside this session's
memory, called out explicitly, not swept in silently.

## Acceptance
#682 + #683 bodies read as finished decision-records; #686 filed with conditions + success signal; two
memory files written + indexed; S116 memory residue durably homed. sync_check at start: 47✅/12⚠/4❌ —
the 4 ❌ are the known #680 umbrellas (evidence-graded, non-blocking per the S117-in agenda), not worked
around.

## Carried into S118
**Drive to V15-ready, starting with #671** (V13→V15 migration-with-data). See the S118 agenda. The
Beaverdam work (#682/#683/#686) is decided + scoped — concurrent Linus track may begin independently;
attention-competing work waits for V15-ready.
