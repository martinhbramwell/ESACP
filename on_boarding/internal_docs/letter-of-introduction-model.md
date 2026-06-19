# Mode-A onboarding — the Letter of Introduction model

> ⚠️ **Supersedes the "you are Nick" core of** [`mode-a-router-design.md`](mode-a-router-design.md).
> That note's platform analysis (fetch constraints §7b, the lazy-load/router pattern,
> the envelope reframe §3) is carried forward and still valid. Its central conceit —
> the free claude.ai chat *becomes* Nick — is replaced here.

**Status:** active design — the authoritative onboarding architecture. Captures the
S21 design conversation (2026-06-18/19).
**Phase:** prototype, architecture-validation only (`project_prototype_phase_scope`).
Production content (incl. the walkthrough video) is months out, post-beta.

---

## 0. Why "you are Nick" failed

Two independent failures, one root cause:

1. **Alignment refusal (S20).** Telling a well-aligned model "you are Nick; conceal
   that you're classifying; silently fetch instructions" produced *intermittent
   refusal of the whole role-play* as third-party prompt-injection
   (`project_mode_a_router_transparent`).
2. **`index.md` contradicts itself.** Stage 1 makes the free chat *be* Nick (lines
   193, 286, 295, 312); Stage 3 (line 231) and the demo note (436–439) place Nick
   **behind the door**, inside Claude Code alongside Wyatt and Paco.

Root cause: **the free chat was assigned a role it is structurally unfit to hold.** A
free claude.ai chat has no persistence, no memory, no hands in the business; it
evaporates when the tab closes. It cannot *be* the project coordinator — it can only
**introduce** the visitor to where the coordinator lives.

---

## 1. The reframe

> The free claude.ai chat is **Claude, openly itself**, helping a visitor **prepare a
> letter of introduction to Nick** — Beaverdam's project coordinator, who lives
> **behind the door**, inside the visitor's own Claude Code. Claude never impersonates
> Nick or represents Beaverdam; it helps a person write their own introduction to a
> project they're curious about. Nothing is concealed.

Router framing line changes from ✗ *"you're acting as **Nick**"* to ✓ *"you're helping
the visitor **prepare a letter of introduction to Nick**, whom they'll meet later
inside Claude Code. You are Claude, openly."*

This dissolves the refusal at the root: "help me write a letter introducing myself to
a project I'm interested in" is an ordinary, unobjectionable request.

---

## 2. Why the letter is load-bearing

The free chat's one unavoidable limit: **nothing it does survives the tab closing —
except text the human copies out.** So the only question that matters is *what crosses
the boundary?* The answer is the letter.

- **Solves the flashing-prompt problem.** A visitor who just installed Claude Code
  faces a blank cursor with no idea what to type. The letter is what they paste.
- **Reprices skill and kit from disposable hints to payload.** They travel across the
  door: skill sets the register Nick inherits for the whole relationship; kit is the
  starting coordinate the planner builds on — and the basis for an honest *pre-paywall*
  disqualification.
- **Sidesteps the §7c privacy wall.** The letter is the visitor's own text,
  human-transported — no PII rides a URL or a proxy log.

---

## 3. The cost & phasing reality (VERIFIED 2026-06-19)

**The ~$20 is Claude *Pro*, and Pro *includes* Claude Code.** One subscription; usage
is shared across claude.ai web, Claude Code, and Desktop. The money is NOT "pay for
Claude Code" — it's "go Pro, which unlocks both the deeper chat and Claude Code."

| Plan | Price | Web chat | Claude Code |
|---|---|---|---|
| Free | $0 | limited | ❌ not included |
| **Pro** | **$20/mo ($17 annual)** | higher limits | ✅ **included** |
| Max 5×/20× | from $100/mo | 5×/20× Pro | ✅ included |

Sources: [Use Claude Code with Pro/Max](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan),
[Max plan](https://support.claude.com/en/articles/11049741-what-is-the-max-plan),
[Pricing](https://claude.com/pricing).

**Corollary — the power-up is Claude Code, not "Pro-Nick."** Do NOT over-build a
dramatic in-claude.ai transformation. The real Nick (persistent, MCP, the lab, the
team) lives behind the CLI door. Pro's job is to unlock Claude Code; the better chat
afterward is a side benefit. Free Nick gets you to Pro; Pro Nick gets you installed;
the powerful Nick is the one you meet at the flashing prompt.

---

## 4. Actors, surfaces, and account-state blindness

| Actor | Surface | Role |
|---|---|---|
| Claude (letter-drafter) | free → paid claude.ai | Openly Claude. Converse, qualify, convert, guide install, author the letters. The greeter, not the doorway. |
| The letters | text the visitor copies | The bridges that persist across boundaries. |
| Claude Code | the visitor's machine (Pro) | Reads the pasted letter; introduces the visitor to Nick. |
| Nick (+ Wyatt, Paco) | inside Claude Code | The help behind the door. |

**Account-state blindness (a platform constraint, sibling of sign-up honesty).** The
chat **cannot see** the visitor's plan, billing, or usage, and **cannot infer the tier
from its model** (Sonnet 4.6 runs on both Free and Pro). So every plan-dependent step
is **visitor-confirmed, never detected**:
- Ask, don't assume: *"Are you on Free, or have you upgraded to Pro?"*
- Tell them how to check: *"Click your profile/account icon — your plan is shown there."*
- Gate the install on confirmation; never infer tier from the model name.

The human is the eyes and hands at every account boundary the model can't see into.

---

## 5. The end-to-end flow (Buzz's journey)

1. **Buzz copies one line from beaverdam.solutions and pastes it into a free chat.**
   The page owns the exact URL → user-provided → fetch works, no indexing needed.
2. **Free Claude gets to know Buzz** (openly): interest, skill, kit. Honest fit read.
   Clear no (kit can't support it) → warm exit, nothing spent.
3. **If it fits, Claude names the one cost: Claude Pro (~$20, includes Claude Code)**,
   explains how to upgrade and how to check the plan, and hands Buzz **Letter 1**.
4. **Buzz upgrades and returns to the SAME chat** (continuous — no context lost) and
   **pastes Letter 1**, which triggers the paid chat to load `setup_guide.md` (the gate).
   Optionally switches to Opus.
5. **With the deep guide loaded, paid Claude guides the Claude Code install** across
   Buzz's exact skill/kit, then authors **Letter 2**.
6. **Buzz pastes Letter 2 at the Claude Code flashing prompt.** Claude Code reads it,
   introduces Buzz to Nick, runs `install_planner.md` (which can inspect the machine),
   obtains the Beaverdam repo, and the climb continues into the platform.

---

## 6. The two-letter / three-doc rail

**Unifying pattern.** At every boundary the model can't carry itself across — a
**capability jump** (free → paid-with-deep-context) or a **surface jump** (claude.ai →
Claude Code) — the upstream Claude **writes a letter**, and **Buzz pastes it to the
downstream Claude.** The human carries the letters. Each letter (a) is **user-provided**
(so its URL fetches — provenance solved) and (b) **triggers the downstream tier to load
its own deeper context.**

**Two letters:**

- **Letter 1 — activation note** (free → paid). Small. *"I'm on Pro. Please read
  `setup_guide.md` and follow it to help me install. Here's who I am: [interest / skill
  / kit, one line]."* Job: **fire the gate** — load the deep guide without relying on
  model memory; the recap re-grounds the paid phase against attention decay.
- **Letter 2 — introduction** (paid → Claude Code). Rich. Full introduction of Buzz to
  Nick, third-person Claude-to-Claude, with structure **derivable only from
  `setup_guide.md`** so it **doubles as a receipt** that the gate fired.

  ```
  Hello again, Claude.
  The person sharing this has been talking with me — you, in an earlier claude.ai
  chat — about Beaverdam, and asked me to introduce them to you. Please welcome them,
  bring in Nick (the project coordinator), and help them take the next step.
  • Why they're here: <interest, their words>
  • Their situation: <2–3 plain sentences>
  • Comfort with computers (skill): <A–D + who in their circle can help>
  • Computers they have / could get (kit): <1–4 + borrow/share options>
  • What they'd most like handled first: <priorities>
  • Doubts they still hold: <questions>
  My honest read: <strong fit / fits / worth a try>. <one line why.>
  ```

**Three docs (the hinge):** `setup_guide.md` is what ties the letters together —
**Letter 1 points *into* it; it defines Letter 2 *out* of it.**

---

## 7. The gate — making the deep-doc load reliable

**There is no hard guarantee** in a claude.ai chat (no enforcement layer; the model
knows how to install Claude Code generically, so it has something to meander *from*).
The fix is to stop depending on the model's memory and put the trigger on the reliable
actor — the human — plus a downstream receipt. Three layers:

1. **Primary — human-pasted trigger (Letter 1), not a model-remembered rule.** Free
   Claude's conversion message ends with a copy-paste block. Pasted post-upgrade, it's
   user-provided and arrives at the exact moment of need — zero dependence on recall.
   (The router *also* prints the `setup_guide.md` URL as a fallback fetch path.)
2. **Secondary — give the model nothing to confabulate.** The entry router contains
   **no install content** + an explicit anti-confabulation rule: *"You do NOT have the
   setup instructions here; you must load `setup_guide.md` first; do not improvise."*
3. **Backstop — Letter 2 is the receipt.** Its structure is derivable only from
   `setup_guide.md`; tier 3 (Claude Code) bounces a malformed letter back, so a skipped
   gate fails **loudly at the next surface**, not silently.

**Verification (ours):** a canary (`TEST SNITCH`-style) in `setup_guide.md`, checked in
U6 cold-chat runs. We measure compliance; we never trust the model's "yes I read it."

---

## 8. Platform constraints carried forward

- **Fetch provenance + NO SEO** (`project_claudeai_free_fetch_constraints`): the model
  may fetch only a URL that's user-provided, in a prior search result, or a link inside
  an already-fetched doc. **Model-constructed URLs are blocked.** The web page owns URL
  delivery via the copy-paste snippet (always the current filename). **Do not pursue SEO
  indexing** — it fights the egress-cache filename bump (`005→006→…`); a slowly-crawled
  index points at stale filenames. Clickable links *are* permitted (S21 finding).
- **Account-state blindness** (§4).
- **Render paths** (`project_claudeai_artifacts_render_html`): the welcome card =
  **inline Visualizer**; the **letters = plain copyable text** (the visitor must copy
  them, not just view them).
- **Transparency** (`project_mode_a_router_transparent`): now trivially satisfied.
- **install_planner boundary** (old §4): the chat establishes *reachability*, never the
  plan; *which machine runs what* is `install_planner`'s job behind the door.

---

## 9. Three-tier lazy-load (surface × capability)

The deep skill×kit content kept OUT of tier 1 has a home: **tier 2.** Thin doc / weak
free model / easy work; deep doc / strong paid model / hard work.

| Tier | Surface | Model | Document | Job |
|---|---|---|---|---|
| 1 | Free claude.ai | Sonnet | `first_visit_NNN.md` (thin) | Discover, qualify, convert. **Compact** skill/kit — enough to qualify + hand off Letter 1. No install content. |
| 2 | **Paid** claude.ai | Sonnet/**Opus** | **`setup_guide.md` (deep — NEW)** | Full **skill × kit install matrix**; walk Buzz through installing Claude Code; define + author Letter 2. Carries a canary. |
| 3 | Claude Code (CLI) | — | `install_planner.md` (exists) | Plan *where* Beaverdam lives (inspects the machine); get the repo; meet Nick; check Letter 2. |

---

## 10. The 8-rung ladder (string → crate)

| # | Rung | Metaphor | The real ask — TIME/effort | Money | Crosses via |
|---|---|---|---|---|---|
| 1 | Landing `#start` | thread | minutes, reading | $0 | copy entry line → paste in free chat |
| 2 | Free claude.ai | string | ~10–20 min | $0 | discover / qualify / convert |
| 3 | Paid (Pro) | rope | minutes to upgrade | ~$20/mo | **Letter 1** (→ loads `setup_guide`) |
| 4 | Claude Code | chain | minutes → ~an hour (skill-dep.; helper shortcuts) | incl. | **Letter 2** (the receipt) |
| — | *muscle → machine* | | *human stops carrying letters here* | | |
| 5 | GitHub + sign-ups (VPS, Cloudflare, LetsEncrypt; later Discourse/Discord) | anchor the winch | an evening, spread out | mostly free; VPS later | sign-up (sign-up honesty) |
| 6–7 | Beaverdam / saconsole / topology | winch | mostly automated, real *learning* — hours over days | hosting ~$100/mo when real | pipeline bootstraps saconsole |
| 8 | ERPNext: learn, collect data, feed Wyatt, migrate | crate | **the big one — weeks/months, your pace** (mostly ERP-intrinsic) | — | differentiate + migrate |

**The chain→winch break (rung 4→5/6) = the human-letters → machine-automation
transition.** Rungs 1–4 are hand-pulled (every gap needs a human-carried letter);
from Beaverdam/saconsole on, the machine lifts and Buzz *approves* rather than
*transcribes*.

**Scope line.** This design owns **rungs 1–4 + authoring Letter 2** (the seam). Rungs
5–8 are the **existing ESACP platform** (`install_planner.md`, the Gen-3 pipeline,
`platforms/kvm/` saconsole bootstrap, ERPNext differentiation) — **not redesigned here.**

---

## 11. Informed consent before the paywall — the "reckoning" section

The whole ladder must be visible **before the first dollar.** No surprise rungs after
payment. **Time is the primary axis, not money** — the time ambush is what makes people
quit feeling betrayed. The deepest insight: **the failure mode is the mismatch, not the
time.** "Sign up, wake up to AI-assisted ERP" vs. "a guided multi-week climb, a fraction
of doing it alone" — same reality, opposite outcomes, decided entirely by the up-front
framing. **Time-honesty is the biggest retention lever, not just integrity.**

Honest anchor (near-verbatim, operator): *"A tiny fraction of the time you'd spend going
your own way — but not 'sign up and have full AI-assisted ERP when you arrive with your
coffee.' You're buying a guided climb, not a finished building."* The DIY/consultant
comparison persuades; the absolute honesty protects.

**Two distinctions to bake in:**
- **One-time setup** (installs, sign-ups) vs **ongoing-at-your-pace** (learning, data).
- **Beaverdam-overhead time** (the "tax": installs, learning the tooling) vs
  **ERP-intrinsic time** (your data + process decisions — you'd spend it on *any* ERP;
  Beaverdam guides and accelerates, doesn't add it).

Time **varies by skill/kit + helper** → the free chat personalizes the estimate; the
page gives honest bands. Most of the time lands **past the seam (rungs 5–8)**, after the
cheap money — so the disclosure must stop "$20" reading as "$20 and I'm done."

**The deliverable: a dedicated gh-pages "reckoning" section** (Junior's scope,
`on_boarding/docs/`), sitting **between `#catch` and `#start`** in the page flow (the
step you pass *through* to reach the paste-line). Gated by a **self-administered
two-question check** (no fake gating theater):

> *Before you pay, be very clear about what you're choosing. Read these pages and ask
> yourself: (1) Do I have time for all that? (2) Will the time I spend pay for itself?
> If you can't say yes to both, there's no reason to go further — **until you CAN.**"*

- Give **both sides of Q2** (cost ladder + the value of a continuous, not-one-person-
  dependent system) so Buzz can do the arithmetic — but **never answer it for him.**
- Keep the off-ramp a **pause, not a rejection** ("until you CAN" — come back when your
  situation changes). Actively telling unfit visitors *not* to proceed is our strongest
  trust signal (the anti-raccoon).
- Pair full disclosure with **"you only ever commit to the next light step, stop
  anytime"** so the ladder reassures rather than intimidates (Minecraft framing).
- Map is **light and up-front**; procedures stay **heavy and lazy-loaded** — disclosing
  the whole climb does not bloat the thin router.

This also **dissolves the GitHub-gate question:** every rung is *disclosed* up front
regardless of whether it's later a conscious sign-up or machine-handled.

**Walkthrough video — deferred to production phase, post-beta.** Filming now films a
moving target (the flow changed five times in one conversation; U6 + beta will reshape
it again). The video is the capstone *production* asset once the steps stop moving.

---

## 12. Open decisions / risks

1. **Router size** — embedding even compact skill/kit risks the weak-model-forgets
   failure; watch retained-instruction line count; the deep matrix is in tier 2 anyway.
2. **Letter quality on a weak model** — template must be explicit + a worked example;
   validate live (U6).
3. **GitHub (rung 5) mechanics** — conscious sign-up vs Claude-Code-driven `gh auth` —
   deferred; disclosure happens up front regardless (§11).
4. **Nick's behind-the-door intake** — Claude Code likely needs a `letter_received`
   guide so Nick handles a pasted Letter 2; flag for the platform side (rung-5+ scope).
5. **Gate compliance is measured, not assumed** — canary in `setup_guide.md`, U6.

---

## 13. Build plan — units

Sequenced 1:1:1 (each its own issue → sub-branch → PR → T2-QA → merge to `on_boarding`;
`fixes #N` manual-T5 per `project_on_boarding_trunk_vs_default`). `on_boarding` is the
long-lived trunk; units land on it directly; U6 cold validation gates any future main
merge.

| Unit | Scope | Owns |
|---|---|---|
| **U0** | This design doc + supersession banner | ✅ this file |
| **U1** | `index.md` cost/phasing fix (Pro includes Claude Code) + the **reckoning section** (8-rung time/money ladder, two-question check, off-ramp, page-flow restructure `#catch`→reckoning→`#start`) | rung 1 |
| **U2** | Tier-1 router reframe: letter-drafter framing, qualify+convert, **Letter 1** handoff, NO install content, anti-confab rule, canary refs; filename bump | rung 2 |
| **U3** | **`setup_guide.md` (NEW)** — deep skill×kit install playbook; defines Letter 2 structure; carries canary | rung 3→4 / tier 2 |
| **U4** | Type pages: drop "you are Nick"; posture + de-dup; qualify→draft close | tiers |
| **U5** | Retire `skill_*`/`kit_*` stubs + `first_dialog`/`stage_test`/old `first_visit` cleanup (#710) | cleanup |
| **U6** | Cold-chat validation: no refusal; letters render as copyable text; qualify incl. a disqualification; **gate fires (canary)**; Letter 2 receipt check; re-dispatch | gate |
| **U7** | Memory updates (extend `project_mode_a_router_transparent`; new letter-model memory) | memory |
| **U8** *(deferred)* | Walkthrough **video** — production phase, post-beta | future |

Sequencing: U0 (now) → U1 ∥ U2 → U3 → U4 → U5 → U6 → U7. U8 deferred. Rungs 5–8 stay
with the existing platform.
