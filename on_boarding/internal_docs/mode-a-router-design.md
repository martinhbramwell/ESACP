# Mode-A persona — router architecture (design note)

> ⚠️ **SUPERSEDED (in part).** The central conceit of this note — the free claude.ai
> chat *becomes* Nick ("you are Nick") — is replaced by
> [`letter-of-introduction-model.md`](letter-of-introduction-model.md): the chat is
> openly Claude, helping the visitor draft a **letter of introduction** to Nick, who
> lives behind the door inside Claude Code. The platform analysis below (fetch
> constraints §7b, the lazy-load/router pattern, the envelope reframe §3) is still
> valid and is carried forward. Read the letter-model note first; treat this as
> background/provenance.

**Status:** design note for review — not yet built. A stepping stone, not a spec.
**Phase:** prototype, architecture-validation only (`project_prototype_phase_scope`).
**Lineage:** evolves the single-doc `first_dialog.md` (v3 → v4, ESACP#695). Sits beside
the install-planner boundary (#601/#602) and the entry-architecture thread (#448).

---

## 1. The problem this solves

The Mode-A persona is one served markdown doc that a cold visitor's free-tier
Claude fetches and *becomes* ("you are Nick"). Two live failure modes drove this
redesign:

- **Size vs. completeness tension.** v3 (316 lines) was complete but a weak/free
  model **forgot it** a few turns in. v4 (129 lines) survives in context but is
  **too thin to handle anything off the happy path** — see the Test006 run, where
  Nick install-planned, nearly disqualified a technical visitor, and twice
  undercut the product ("you could just run Claude Code without Beaverdam").
  A single document cannot escape this trade-off on a weak model.

- **Meander.** With no single terminal objective in view, Nick "just chats" —
  reasoning from the "helpful Specialist Expert" frame, which pulls him toward
  *solving the visitor's stated problem* instead of doing his actual job.

The fix is structural: **a thin router that lazy-loads one focused handler.** The
model only ever holds *small ∩ relevant*, while total coverage stays large —
the same pattern the project already trusts (`first_dialog.md → install_planner.md`),
pushed one level earlier and made a pick-list.

---

## 2. The goal of the conversation (mission-grounded)

A free claude.ai chat is **structurally incapable of the mission**: no
persistence, no MCP hands inside the business, no lab, no GitHub institutional
memory. The chat evaporates when the tab closes — the opposite of the mission's
"durable records / continuity for a family that can't lose context." So Nick can
never *be* the thing; he can only be the **door** to where the mission happens
(paid Claude Code → `install_planner.md` → the lab → MCP → the durable record).

> **Terminal objective.** Move a cold visitor to one honest decision about the
> single threshold that unlocks the mission — install Claude Code and run the
> `install_planner.md` handoff — or a clean, honest "no / not-yet" exit.
> **Nick is a triage-and-threshold agent, not a support agent. He is the doorway,
> not the help. The help lives behind the door.**

Per-turn test Nick applies to every sentence: *does this move toward decision +
handoff (or a clean exit)? If it's chatting, advising, or planning — it's failing.*
A clean "not for you" is a **success**. Solving the upgrade in-chat is a **failure**.

---

## 3. The actor is an envelope, not an individual

Critical reframe: the visitor is **not** a person with two fixed attributes. It is
an owner-operator **plus a mobilisable envelope** — people (family, friends,
employees, investors) and acquirable kit (buy, rent, borrow, share). This is not
an edge case bolted on; the mission names *"family members"* and the vision names
*"the owner, family and staff"* — **the human network is first-class in the mission.**

Consequences:

- **Skill and hardware are the *current coordinate*, not a ceiling.** Both are
  relaxable by reaching into the envelope.
- **Skill is fillable from the network.** A low-skill owner is not a dead end if
  there's a techy nephew / an Excel-fluent bookkeeper / a daughter who runs the
  website. Beaverdam's premise fits: the helper *bootstraps*, then steps back; the
  owner stays the boss.
- **Hardware is fillable from the envelope.** Phone-only is not stuck: used-PC
  rung, borrow a tower, an employee's spare, a short-term VPS.
- **The lever is shared — relaxation is coupled.** One relationship can move both
  axes at once (the nephew who has a spare Linux box). So the cells are *not*
  independent; the cheapest first move depends on the *combination*.
- **New sub-goal: locate the helper relationship.** What determines reachability
  is often not the owner's personal skill but *who in their orbit can cross the
  technical threshold with them.* Qualifying includes discovering that person.

---

## 4. Conversation flow

```
1. WHY (posture)          — why are they here? sets whether conversion is even the goal
2. current coordinate     — skill (A–D) × hardware (1–4): where they stand today
3. broaden the envelope   — who and what can they mobilise? (helper + kit)
4. reachability verdict   — honest fit over the *reachable* config, not the current one
5. convert / exit         — Claude Code + install_planner.md handoff, or clean exit
```

A "not feasible alone" becomes "reachable with your nephew + a used box" — a more
honest and more often *yes* verdict.

**Guardrail.** Broadening stays at *"is a viable path reachable?"* — never *"here's
the plan."* *That* a helper exists and *that* a used PC is affordable is feasibility
(Nick's job). *Which machine runs what, who installs which piece* is the plan —
still `install_planner.md`'s job, behind the door. Otherwise we re-open the
"you are not planning the installation" trap, now with people added.

---

## 5. Taxonomy

### Axis 0 — WHY (primary triage; sets the terminal posture)
1. **Curious / student / journalist / tourist** → goal is **inform, not convert.**
   Learn-more links, the open GitHub record, zero pressure. "Thanks for looking" = success.
2. **Owner, generalised information-management mess** → **qualify-and-convert**, gentle, anchored.
3. **Owner, well-understood problem** → **convert fast** — pre-qualified; deliver the threshold + handoff.

### Axis 1 — skill (register + the "why Beaverdam vs. raw Claude Code" answer)
- **A** — lots of computer experience incl. programming; optimises own WiFi.
- **B** — regular multi-system user; Excel, TurboTax, own website.
- **C** — some MS front-office; or a Mac "'coz it's intuitive."
- **D** — smartphone and a filing cabinet.

### Axis 2 — hardware/access (coarse feasibility only; defers detail to install_planner)
- **1** — access to numerous machines and networks.
- **2** — several machines on one LAN.
- **3** — laptop and WiFi.
- **4** — smartphone.

The 4×4 (a1…d4) is a **map of starting coordinates**, each with a characteristic
gap and a characteristic cheapest broadening move.

---

## 6. File architecture (compose from playbooks; don't write 16 essays)

The dynamic/envelope view legitimises richer per-cell content (broadening is
genuinely combination-dependent), but 16 hand-written essays would be 16× the
drift surface — a fault factory, against the mission's low-fault principle. Middle
path: keep the 16 cells as the **map**, author them from shared **playbooks**.

- **`first_dialog.md` — thin router (~50 lines).** Welcome + WHY triage + the
  universal invariants that must never be lost (the one cost; sign-up honesty; the
  §1.5 silent-re-fetch / never-claim-empty rule; the §2 terminal "you are the
  doorway" goal) + dispatch to one WHY file.
- **3 WHY files** (`visitor/curious.md`, `visitor/owner_general.md`,
  `visitor/owner_specific.md`). Each embeds a **compact A–D register guide** and a
  **light 1–4 feasibility guide**, plus its convert/exit close. (Embedding keeps
  fetch count low — see §7.)
- **2 broadening playbooks** referenced by the WHY files:
  - *skill-relaxation* (rows A–D): how to surface and frame the helper relationship.
  - *resource-relaxation* (cols 1–4): buy / rent / borrow / share; the used-PC rung.
- **Per-cell "first move from here"** — one paragraph naming the cheapest *coupled*
  relaxation for that coordinate (D4 ≠ B2). Small, mostly references the playbooks.
- **~2 named exception handlers** for true interaction cells:
  `expert_already_running.md` (the Test006 fix — don't disqualify, don't
  install-plan, answer why-Beaverdam, convert fast) and the phone-only/used-PC rung.

Net: ~6–8 small focused files, **3-way primary classification** (far more robust on
a weak model than a 16-way pick, where cells like D1 or A4 are near-contradictory).

---

## 7. Open decisions & risks

1. **Fetch reliability is the riskiest part.** Every extra fetch is a failure
   point, and a *cold non-technical* visitor cannot rescue a failed fetch (lesson
   from the first live transcript). Mitigations: router (in context) fetches **one**
   WHY file that *embeds* its skill/hardware notes (no second hop); §1.5
   silent-re-fetch applies to the WHY file too; define a **degrade-to-inline**
   fallback if the WHY file genuinely won't load, rather than stalling.
2. **Classification robustness.** Infer A–D / 1–4 from the welcome's open answers;
   do **not** interrogate (meander risk). "When unsure, ask exactly one
   disambiguating question, then classify."
3. **Where do universal invariants live?** Recommendation: **router-only**
   (centralised — short, kills drift). Trade-off: router + WHY file must coexist in
   context. Alternative (self-contained WHY files) = duplication + drift.
4. **Install_planner boundary.** The hardware axis must stay coarse; broadening
   establishes reachability, never a plan. Watch for the §0 planning trap.
5. **Authoring model.** 16 bespoke files (rejected: drift) vs. playbooks + map
   (recommended). Revisit only if cells prove to need genuinely bespoke prose.

---

## 7b. VERIFIED platform constraints — free-plan web tool (live tests, S19)

Memory: `project_claudeai_free_fetch_constraints`. Findings from mode-2 (free
test004/006 accounts):

1. **Provenance rule (load-bearing).** The model may only fetch a URL that
   appeared in a prior web_search result, a prior fetch result (a link inside an
   already-fetched page), or was user-provided. A model-*constructed*, never-seen
   URL is refused: *"This URL was not in any prior search or fetch result.
   web_search for it first, then fetch the result link."*
2. **POST blocked** (not cleanly separable from the provenance block, but no HTTP
   POST from the chat regardless).
3. **Query-string caching.** Within one conversation, GETs to the same host+path
   differing only in query string return the FIRST cached body (original param
   *values* came back despite different params sent).
4. **Redeploy-to-same-path serves STALE across conversations (TTL-bound).** After
   deploying #699 to `first_dialog_router.md` (fresh at origin via curl), a new chat
   (Test008) still fetched the old #697 body through the egress proxy. The earlier
   "cross-conversation is fresh" note was TTL expiry over time, **not** guaranteed
   freshness — corrected. **Cache scope (per-account vs global) and TTL are UNKNOWN**
   — so we cannot assume even a fresh-account cold visitor gets current content after
   an update. Mitigation: bump the filename every publication (`first_visit_NNN.md`);
   only a new path/host busts the cache (query strings are ignored). The router is
   now served as `first_visit.md` (was `first_dialog_router.md`).

**This decides the architecture:**
- Dynamic `?interest=…&skill=…&kit=…` endpoint = **dead** (constructed URL blocked +
  query-cache + no POST). Static **pick-list of distinct paths** is the only option.
- **HARD REQUIREMENT:** the pick-list class-file URLs **must be printed verbatim in
  the router doc** (`first_dialog.md`), so once it is fetched those URLs are "in a
  prior fetch result" and the model may fetch the one it picks. The model **selects
  from the printed list, never constructs** a URL. This is the platform's own
  sanctioned "fetch the result link" path.
- Genuinely dynamic per-request state (#448 brain-dump persistence) must go through
  the **MCP connector (a tool call)**, not HTTP fetch/POST.

**OPEN — make-or-break (not yet tested):** does a link *printed inside a fetched
doc* actually become fetchable by the model, AND does that second (different-path)
fetch return fresh content? Decisive test using files we already serve: one chat —
(1) user pastes & fetches `first_dialog.md`; (2) ask the model, *without* pasting
the URL, to fetch the `install_planner.md` link printed in its §7. Returns
install_planner's own heading → router viable. Refuses / returns first_dialog again
→ router dead.

**Fallback if it fails:** abandon lazy-loading; ship a single **compact
decision-tree** `first_dialog.md` — small enough to retain, a branch table
(WHY→posture, A–D→register, 1–4→feasibility), zero second fetch. Less rich, maximally robust.

## 7c. Rejected: rotating-GET state collection (and why connector is the right tool)

Idea explored (S19): rotate subdomains (`round1.`, `round2.` … `*.beaverdam.solutions`
wildcard cert) and pack the visitor's reply into a query string the model fetches,
so a real nginx backend records each Buzz's status and returns fresh per-round
guidelines.

- **Good part:** rotating the *host* defeats the per-conversation cache (§7b #3)
  regardless of whether that cache is host- or path-keyed. Sound cache-buster.
- **Wall 1 — provenance.** The scheme needs the *model* to construct
  `roundN…?user_response=…`, a never-seen model-built URL → refused (§7b #1). The
  sanctioned "fetch the printed link" path can't help: a link carrying the reply
  can't be pre-printed because the reply doesn't exist until the visitor speaks.
- **Wall 2 — privacy (decisive on its own).** Packing a small business's free-text
  brain-dump into a URL violates the no-sensitive-data-in-URLs rule and scatters it
  in cleartext across egress-proxy, nginx, and intermediary logs; plus URL-length
  caps (~2–8 KB) choke a long reply. (A wildcard cert is normal TLS, not an
  "exploit," and TLS is orthogonal to the tool-layer provenance rule.)
- **Right tool for the goal.** Recording Buzz status + returning dynamic guidelines
  is achievable via the **MCP connector (a tool call)** — structured args (no PII in
  URLs, no length cap), bypasses fetch caching/provenance. This is the #448
  brain-dump-persistence + `project_claudeai_free_connector_capability` path, with
  the known cold-visitor setup friction (settings step, "unverified service"
  warning, directory-vetting). An enhancement layer for warm/returning visitors,
  not the cold front door.

→ **Verdict:** stateless pick-list router now (no server, no collection);
server-side Buzz-status collection is a connector-era upgrade on top.

## 7d. Build decisions (this scaffold)

- **Fold playbooks + exception handlers INTO self-contained WHY files.** The §7b
  fetch constraints make every hop a liability, so the router does **exactly one
  extra fetch**: a single WHY file that carries its own A–D register, 1–4
  feasibility, envelope-broadening, exception branches (expert-already-running,
  phone-only), and close. No separate playbook/exception fetches. (Supersedes §6's
  multi-file sketch.)
- **Build under staging names; do not touch the live front door yet.** Ship
  `first_dialog_router.md` + `visitor/*.md` additively. The live `first_dialog.md`
  (v4) stays the front door until the §7b printed-link make-or-break test passes
  against the *real* deployed router; only then promote router → `first_dialog.md`.

## 8. Next step

If this design holds: file an issue, cut a sub-branch, scaffold the router +
3 WHY files + 2 playbooks + 2 exception handlers, then a fresh mode-2 run against
the Test006 scenario (expert / already-running) to confirm the conversion lands.
If it doesn't hold — find the next stone.
