# Entry-architecture notes — Buzz's path from first contact to a working controller

## Status

**Exploratory. Pre-decision. Not a committed architecture.**

Captured 2026-05-22 during Session 3 of the `on_boarding` branch as the
operator and Junior worked through several layers of clarification on
the role model and the actual mechanics of getting Buzz from "I just
heard about ESACP" to "Essex is building a controller on a machine I
own (or rent)".

These notes are a thinking document. Treat them as the substrate for
future architectural decisions, not as decisions themselves. Where
choices are listed, they are **option spaces still open**, not picked
paths.

## Why this file exists

Through Sessions 1–3 the `on_boarding` kit has built increasingly
downstream artefacts (cadence rules, Buzz-perspective lens, Stage-2
triage, `bootstrap.py` v0). The `bootstrap.py` v0 in particular
assumes Buzz is *already at* a working Ubuntu/WSL2 terminal — a
condition that requires several earlier stages to be solved, none of
which the kit had previously articulated.

This document is the missing upstream architecture.

---

## 1. The role model (corrected version)

Earlier in the kit's life, Buzz was a single static archetype
(heirloom moving, low tech-comfort) and Essex was a separate
broader-project Claude on a different controller. The operator
clarified the model significantly in Session 3:

- **Junior** — director and corpus curator. Owns the `on_boarding`
  branch and kit. Orchestrates iterations between Buzz and Essex,
  captures durable artefacts, files issues for gaps, refines the
  pre-canned discovery question set, decides what ships.
- **Buzz** — SME-owner *role* (not a fixed person). Researches a
  real, plausible Eastern-Ontario small-business IT environment per
  iteration (small auto-repair shop, two-truck delivery outfit,
  indie law office, pianos-and-antiques resaler, etc.) by reading
  the real world (web research). Stays in character within a cycle;
  resets between cycles.
- **Essex** — ESACP platform expert. Two operating modes:
  - **Mode A — pre-canned discovery.** Walks Buzz through a fixed
    question set (hardware, network, current software, business
    need) to establish the initial state. The question set is
    itself a Junior-curated artefact that evolves across iterations.
  - **Mode B — ad-hoc guidance.** Once the initial state is known,
    Essex departs from script and converses naturally — explaining,
    proposing, evaluating, sometimes saying "this is outside ESACP's
    current range, but here's an alternative."

Essex's voice — per operator directive 2026-05-22 — is **intrusive
but not threatening, instructive but not overwhelming, supportive
but not condescending.**

### Essex's competence boundary

- **Solid capability** (Essex commits firmly): the ESACP topology,
  dev VMs with ERPNext V16, the bench/Frappe app catalogue, the
  Cytoscape control plane and what it lets Buzz do without typing
  commands, BaRe snapshot/restore.
- **Ad-hoc capability** (Essex evaluates honestly): integration
  requests beyond the shipped surface. Example: "Can I integrate my
  Square dual-screen POS?" — Essex consults the Frappe app catalogue,
  estimates effort in plain language, says when something is
  straightforward, multi-week, or not realistic.

**Essex is allowed to reference ESACP-as-planned, not only
ESACP-as-shipped.** Per operator (2026-05-22): "The whole point of an
AI-assisted platform is to provide the kinds of integration and
development expertise SMEs cannot afford. Has to be honest and
grounded in fact, yes. Has to be limited to what we have at the
moment? No." Essex must not fabricate apps or claim
non-existent integrations work — but Essex *can* honestly evaluate
"this isn't there yet, here's how hard it would be to add."

### Junior's role in iterations

Junior does **not** roleplay either persona. Junior orchestrates,
captures, synthesises. Per operator (2026-05-22), the value of each
iteration is **both** the structured archetype profile *and* the
transcript with Essex's reasoning visible — the transcript is
Essex's training corpus; rereading old transcripts is how Essex
sharpens against the next Buzz.

---

## 2. The trace from "Get Started" tap → Essex building the controller

### Stage 0 — First contact (Buzz on iPhone or laptop browser)

**What exists today**: `docs/index.md` on GitHub Pages — descriptive
landing page, no call-to-action wired up.

**What's missing**: a "Get Started" affordance, which has to
connect Buzz to a live Essex conversation.

**Most likely target**: a chat widget powered by the Claude API.
This is the only option that supports Essex's Mode-A discovery
dialog *and* the Mode-B ad-hoc guidance Buzz needs to find a
controller-build path that fits his real environment. Alternative
forms (static form, email-and-wait, Telegram deep link) sacrifice
the live conversation that is the platform's whole pitch.

### Stage 0.5 — The chat backend (phone-side Essex)

A small server-side relay between the chat widget and the Anthropic
API. GitHub Pages cannot host this (it's static-only); the relay
needs to live somewhere with runtime.

**Backend options considered**:

- **Cloudflare Workers** (recommended starting point). The project
  already has CF MCP infrastructure (`cf-mcp-refresh` in `Cld.sh`,
  `sync_check.sh` section 14). Reuses existing credentials and
  tooling. Free tier comfortably covers early traffic.
- GitHub Actions / "lambdas" — these are CI/CD runners, not
  request-serving infrastructure. 20–60s cold start, no streaming,
  rate-limited. Wrong tool.
- Fly.io / Vercel / Render — fresh infrastructure, more capability
  but more credentials to manage.

### Stage 1 — Mode-A discovery dialog (in the chat widget)

Essex walks Buzz through the pre-canned question set. Outputs a
**Buzz profile**: hardware, OS, network, current software, primary
business need. The profile feeds the controller-build plan Essex
proposes in Stage 2.

### Stage 2 — The handoff (the load-bearing missing piece)

The chat conversation is in the browser. To build a controller,
*something* needs privileged access to either Buzz's local machine
*or* a remote VM Buzz controls. The handoff is how that something
gets into place.

Two principal patterns, depending on whether the controller is
local or cloud:

#### Pattern A — Local companion (Buzz's machine hosts the controller)

> **Superseded by §8 (Session-6, 2026-05-24).** The bridge-via-forked-repo
> handoff in §8.5 removes the "ESACP-shipped installer on Buzz's box"
> requirement entirely. The privileged install Buzz performs is **Claude
> Code from Anthropic**, not an ESACP binary — trust handoff to Anthropic,
> not to us. No code-signing surface, no PowerShell ExecutionPolicy
> friction we'd have to engineer around. Pattern A is retained below for
> historical context but is no longer the live design.

- The PWA generates a pairing code or one-line install command.
- Buzz runs it once (PowerShell on Win10, Terminal on macOS/Linux).
- A *companion process* installs on Buzz's box — Claude Code (full
  agentic harness) or a stripped-down ESACP-specific agent.
- Companion phones home with the pairing token; backend pairs it
  with Buzz's chat session.
- Companion now drives Buzz's box; the chat UI continues to be the
  cockpit.

**Friction**: one privileged moment (Buzz pastes a command into a
shell). On Windows: PowerShell ExecutionPolicy warning unless the
script is Authenticode-signed (paid certificate, real annual
cost). On macOS: notarisation; on Linux: distro packaging.
**Net**: real engineering surface, real trust ask of Buzz.

#### Pattern B — Cloud companion (a remote VM hosts the controller)

> **Decoupled from the bridge by §8 (Session-6, 2026-05-24).** The
> cloud-VM provisioning and the chat→Claude-Code bridge are now
> *separate* concerns. Once Buzz is running Claude Code locally
> post-bridge (§8.5), *Claude Code* drives the VM-provisioning dialog
> with Buzz interactively, using Buzz's own provider credentials in his
> own terminal. The PWA does not need to broker cloud credentials. The
> §4 cloud-VM-as-controller value proposition stays intact; what
> changes is who orchestrates it (Claude Code post-bridge, not the
> PWA pre-bridge).

- The PWA holds (or brokers) a scoped credential against a cloud
  provider — typically pasted by Buzz from his own provider
  signup, *not* held by ESACP centrally.
- The PWA calls the provider's API directly (or via CF Worker
  proxy) to instantiate a VM with a `cloud-init` blob that
  installs the ESACP companion on first boot.
- Once the VM is reachable, the PWA talks to it over HTTPS.
- Buzz's local machine is *never touched*.

**Friction**: Buzz signs up for the cloud provider (or pays ESACP
to broker), pastes API key (or pays). No installer to build for
Win10/macOS/Linux; no admin escalation; no code-signing surface.

### Stage 3 — The controller does its work

From here the existing kit picks up: `bootstrap.py` (controller
toolkit install), #432 (identity wizard), #433 (browser-driven
GitHub signup + SSH key paste), then the actual ESACP
controller-build steps.

---

## 3. The PWA as front office

A Progressive Web App, served from GitHub Pages, installs as an
app on Buzz's device (iPhone "Add to Home Screen"; Win10/macOS/Linux
Chrome/Edge "Install app"). The PWA:

- Holds the conversation UI.
- Stores conversation state, archetype profile, build progress in
  IndexedDB **on Buzz's device** — no server-side conversation
  database.
- Calls the Anthropic API through a thin Cloudflare Worker (the
  Worker holds only the API key; it does not store state).
- Optionally talks to a companion process via `localhost` HTTP/WS
  (Pattern A) or to a cloud VM via HTTPS (Pattern B).

**Why this is attractive**:

- ~$0 hosting cost (gh-pages free, CF Worker free tier covers many
  thousands of users).
- Buzz's conversation data lives on his device, not on ESACP-the-
  organisation's servers. Strong privacy story for the pitch.
- Survives reboots, network drops; offline-capable for the
  conversation parts.
- No app-store gatekeeping; install is by URL.

**Sandbox boundary** (where the PWA must hand off):
- Cannot run shell commands on Buzz's box.
- Cannot install software.
- Cannot modify system files.
- Cannot elevate privileges.
- *Can* talk to a localhost service (Pattern A) or an HTTPS endpoint
  on a cloud VM (Pattern B).

The PWA is sufficient for "thinking with Buzz." It is not
sufficient for "acting for Buzz" without a companion (local or
cloud) doing the privileged work.

---

## 4. The cloud-VM-as-controller variant (operator-favoured exploration, 2026-05-22)

> **§8 update (Session-6, 2026-05-24)**: the cloud-VM stays as a real
> deployment target, but it is no longer the *first* artefact the bridge
> hands Buzz to. The bridge in §8.5 hands Buzz to **Claude Code running
> in his own ESACP fork**; *Claude Code* then drives whatever Stage-3
> environment the Mode-A profile pointed at — cloud VM (this §4),
> local Hyper-V (Phase C of §4.3), or any other shape that emerges.
> The "rental-bike economics" pitch from §4.2 still holds; what shifts
> is that the orchestrator of the rental-bike step is Buzz's Claude
> Code instance, not the PWA.

### The proposition

Bootstrap controller runs in the cloud, not on Buzz's box. The PWA
drives it via HTTPS. Buzz's machine stays untouched during the
trust-building phase.

### Why it's compelling

- **Sandbox-compatible**: every action the PWA needs is a standard
  outbound HTTPS call. No browser-sandbox prohibition fires.
- **No installer to write**: skips the entire Win10/macOS/Linux
  packaging, signing, elevation surface.
- **Clean isolation**: PWA compromise = at worst, extra VMs on
  Buzz's cloud account costing money. Buzz's home machine and
  existing data are untouched.
- **Operator-noted economic shape**: cloud providers bill by the
  minute. AFK detection + auto-shutdown means Buzz only pays
  pennies a day during evaluation — not the $5–15/month a
  24×7-running VM would cost. Storage persists ($0.50–1.50/mo for
  30–50 GB) but compute is paid only when in use.
- **Rental-bike-as-a-service feel** (operator framing, 2026-05-22):
  "See where this can get you, Buzz." Low commitment, low cost,
  earned trust before any deeper integration is proposed.

### The trust-progression sequencing the operator described

1. **Phase A — Cloud rental**. Buzz tries ESACP via a small,
   metered cloud VM. PWA + Essex demonstrate capability. Costs
   pennies a day. Buzz's local machine: untouched.
2. **Phase B — Demonstrated value**. Buzz has now seen Cytoscape,
   ERPNext V16, BaRe restore — what ESACP actually offers. Trust
   earned.
3. **Phase C — Invite into the walled garden**. Essex proposes
   activating Hyper-V (or KVM, or VirtualBox-fallback) on Buzz's
   own machine. Friction cost is now justified by something
   concrete. Migrate the configuration from cloud-controller to
   local-Hyper-V-controller. Production data lives in Buzz's
   garden.

### Holes Junior poked in this variant (in good faith, operator-requested)

**Real holes**:

1. **CloudStack-pay-by-minute market is thinner than the pitch
   implies.** True CloudStack-based consumer hosters (iwStack, a
   few EU/Asian providers) is a sparse menu. The broader
   "Linux-VM-by-the-hour" market is dominated by non-CloudStack
   providers (DigitalOcean, Hetzner, Linode, Vultr, Lightsail).
   Two ways forward: widen the menu beyond CloudStack
   (provider-agnostic via cloud-init), or accept Buzz sees 2–3
   choices.

2. **AFK shutdown saves compute, not storage.** Stopped VM = $0
   compute, but disk persists at ~$0.50–1.50/month. Real
   "evaluation cost" math: maybe $0.05–0.10/day during exploration.
   Still cheap enough that the pitch holds, but worth being
   precise.

3. **AFK detection has to listen to the VM, not just the PWA.** If
   Buzz starts a 20-minute install and walks away, you can't shut
   down mid-install. Need a "VM is doing real work" signal (CPU
   utilisation, active sessions, in-flight jobs).

4. **Claude in Chrome adds friction.** For Claude-in-Chrome to
   drive provider signup flows, Buzz first installs Chrome →
   installs the Claude extension → grants browser-automation
   permissions. Three prompts where Buzz could bail. And:
   Chrome/Chromium only. Softer alternative: PWA-Essex *walks Buzz
   through* the signup ("click the green Sign Up button, paste
   this, scroll down…") without the extension — slower, but works
   on every browser, lower trust ask.

5. **Scoped credentials are not uniform.** ESACP wants a key that
   can create/start/stop one project's VMs and nothing else.
   CloudStack supports this with sub-domains/projects, but many
   consumer providers (DigitalOcean, Vultr) offer only
   "full-account-access" tokens. Acceptable for evaluation; real
   surface at production.

6. **"Walled garden" needs honest framing.** Once Buzz invites
   ESACP into his Hyper-V, the system is on his network, not the
   internet — but it still needs outbound for ERPNext updates,
   gateway integrations, Anthropic round-trips, customer-portal
   traffic. The fence is real but it has gates.

7. **Rental-bike analogy breaks at the data threshold.** Bike-as-a-
   service: grab, ride, drop. ERPNext-as-evaluation: at some point
   Buzz enters real customer names and invoice data. That data
   then lives somewhere. Even if it's "test data," in a tenant
   handling personal info it matters. Plan an explicit
   data-deletion / data-export path before Buzz puts real names
   in.

**Smaller holes**:

8. **Hyper-V activation has edition gates.** Win10 Home doesn't
   support Hyper-V (only Pro/Enterprise). For Home users,
   VirtualBox is the fallback. The "invite into your garden" step
   must branch on edition.

9. **Migration cloud→local is not just "redeploy."** Buzz's
   customisations, his data, his integrations — all need to come
   with. BaRe (bucket-1 associate) will eventually handle this,
   but it's a real engineering surface, not a click.

10. **Payment methods vary.** PayPal acceptance among CloudStack
    hosters is patchy; most take credit card. Pick the provider
    menu partly on "what payment instrument Buzz is likely to
    have."

### What stays strong despite the holes

- **PWA + cloud-VM as architecture**: clean, ships sooner than the
  local-companion path, sandboxes Buzz's machine during
  trust-building.
- **Rental-bike-first, garden-second sequencing**: drastically
  lowers Buzz's threshold to try. Most onboarding failures are at
  "do I install this?" not at "is the product good?"
- **Earned-trust handoff at activate-Hyper-V time**: Buzz has now
  seen value; the friction cost is justified.
- **AFK auto-shutdown as default-on**: real economic alignment
  between Buzz and ESACP. Buzz pays for what he uses; ESACP
  doesn't burn cloud credit on idle trials.

### Decisions not yet pinned (would be Session-N agenda items)

- **Provider menu** — pure CloudStack (small list, less engineering
  downstream) vs. provider-agnostic via cloud-init (bigger menu,
  write the abstraction once).
- **Claude-in-Chrome vs. walk-through-by-chat** for signup. The
  walk-through pattern is probably the right MVP.
- **Data-fate policy** — what happens to Buzz's data if he stops
  paying, migrates to local, or clicks "stop." Must be in writing
  before first real-data entry.
- **Backend hosting** — Cloudflare Workers confirmed as starting
  point. Worth revisiting if/when scale or feature pressure
  pushes elsewhere.
- **Anonymous-with-token vs. account-first** — operator confirmed
  anonymous-with-token as the least-threatening default. Account
  creation deferred.
- **Laptop-side companion form** (Claude Code vs. ESACP-specific
  lightweight agent) — *resolved by §8 (Session-6, 2026-05-24)*:
  Claude Code, in Buzz's own ESACP fork. The "ESACP-specific
  lightweight agent" branch is dropped — building a parallel
  agent would re-introduce the Trojan-horse surface §8.5 was
  designed to avoid.
- **Doorway choice (§8.3)** — URL-redirect to `claude.ai/new?q=...` /
  MCP-connector on Buzz's claude.ai / PWA+CF-Worker with operator's
  key. Pick-any-two-of-three property over {free for Buzz,
  transcript visibility for operator, free for operator}. Worker
  doorway is the working assumption pending Mode-A iteration #1.
- **Transcript pipeline transport (§8.4)** — CF R2 currently
  leading; webhook-over-WireGuard to LAN box a viable alternative
  reusing existing mesh; IPFS rejected as over-engineered for
  the actual use case.
- **MCP-connector free-tier availability** — open question. Not
  blocking unless the MCP doorway gets picked. If it is picked,
  current claude.ai pricing/feature docs need a verification pass.
- **Landing-page diagram + video production (§8.7)** — required
  trust artefacts, not yet started. Diagram is the Minecraft
  "zone" view (§5 lens). Video splits into an evergreen ~90-sec
  overview and per-provider deep-dives accepted as semi-disposable.
- **Cross-branch artefact graduation (§8.8)** — on_boarding-designed
  artefacts (diagram, video, eventually the production PWA + Worker)
  need a pattern for promotion to root `docs/` (Senior's gh-pages
  territory). No precedent yet; will get one when the first
  artefact is ready to graduate.
- **Anthropic partnership credits** — long-shot business-development
  ask separate from architecture. "ESACP as last-mile onboarding
  funnel for claude.ai" pitch. Doesn't change the design; could
  subsidize Worker-path tokens during a launch phase.

---

## 5. The Minecraft framing (operator metaphor, 2026-05-22)

The operator described the design intent as:

> Beginning AI for a small business is a bit like starting a new
> Minecraft Survival world. You can wander around until nightfall,
> get killed by a zombie, and find yourself back at the beginning.
> My intention is to provide a well-lit, fenced-off zone with
> shelter, food, and tools.

This is the **north-star metaphor** for evaluating individual
deliverables. The mapping:

| Minecraft | ESACP equivalent | Current state |
|---|---|---|
| **Shelter** | Working controller + dev VMs + BaRe snapshots — safe space to experiment without consequence | Partially built (Mighty has it; the bootstrap path for new operators is what this kit is for) |
| **Food** | ERPNext + Frappe app ecosystem — mature, ample, well-stocked pantry | Strong. Frappe has thousands of community apps; the platform is hardened. |
| **Tools** | Cytoscape control plane + AI assistant + audit framework + QA verdict layer | Tools are sharp; the toolbelt is still in pieces |
| **Well-lit** | Audit reports, Cytoscape dashboards, qa-log, session logs — Buzz can SEE what's happening | Lighting is uneven; several rooms still rely on a developer's torch |
| **Fenced off** | Sandboxed AI, sign-off gates, BaRe rollback, QA verdict layer, no-direct-prod-touch | Fence is up; still has gaps |

**As a deliverable evaluation check**: every artefact should make
the zone *better-lit*, the *fence sturdier*, or the *food/tools
more accessible*. If a deliverable doesn't do one of those, it's
probably scope drift.

---

## 6. Current gap inventory

| Stage | Component | State |
|---|---|---|
| 0 | GitHub Pages landing | ✅ exists (descriptive only) |
| 0 | "Get Started" affordance | ❌ not built |
| 0.5 | PWA shell (HTML/JS, service worker, manifest) | ❌ not built |
| 0.5 | Chat backend (CF Worker, Anthropic relay) | ❌ not built |
| 0.5 | Essex system prompt + persona | ❌ not authored |
| 1 | Mode-A discovery question set | ❌ not authored |
| 2 | Pairing-token / handoff backend route | ❌ not built |
| 2 | Cloud-VM provisioning path (CloudStack or provider-agnostic) | ❌ not built |
| 3 | Win-10 stage-0 installer (Pattern A) | ❌ not built |
| 3 | macOS / Linux companion (Pattern A) | ❌ not built |
| 3 | Cloud-VM companion image + cloud-init (Pattern B) | ❌ not built |
| 3 | Session-context transfer chat→companion | ❌ not built |
| 4 | `bootstrap.py` (controller toolkit install on Ubuntu) | ✅ shipped Session 3 (#441) |
| 4+ | Identity wizard (#432), browser signup (#433) | 🔜 planned |

The smallest deployable slice that lets Essex meet Buzz at all is
roughly: **wire a Get Started button → build the PWA shell → stand
up the CF Worker → author the Essex system prompt + Mode-A
questions**. After that there's a phone-side Essex who can converse.

The cloud-VM controller variant (Pattern B) then becomes the next
layer; the local-companion (Pattern A) is plausibly a later
optimisation for Buzzes who don't want a monthly bill.

---

## 7. What this means for the kit's next sessions

- **`BUZZ_PERSPECTIVE.md` needs reframing**. The current doc codifies
  Buzz#1 (heirloom moving, low tech-comfort). Under the corrected
  role model, that's *one archetype*, not *the* archetype. The
  five-point onboarding contract is universal across archetypes —
  keep it. The archetype-specific section becomes
  "first-archetype-example."
- **An ESSEX persona doc is missing**. Essex's character traits
  (intrusive/instructive/supportive), competence boundary
  (solid-vs.-ad-hoc), Mode-A/Mode-B distinction — none are
  documented yet. A companion `ESSEX_PERSPECTIVE.md` would
  formalise it.
- **An archetypes library structure** (`on_boarding/archetypes/`
  directory, one file per archetype with Buzz's profile + Essex's
  proposed path + Junior's gap notes). The bootstrap.py from
  Session 3 is the prescribed path for *one specific Buzz*
  configuration; this needs to become explicit.
- **Iteration mechanism** (in-session role-play vs. subagent
  spawning vs. two literal sessions) — decision deferred until the
  first iteration runs.
- **The entry architecture itself** — the PWA + CF Worker + cloud
  VM stack described here is the first major engineering work the
  kit will undertake. Sessions 4+ will likely move from
  documentation deliverables to actual code (PWA shell, CF Worker,
  Essex system prompt) and back. Session-discipline.md may need a
  small amendment for the mixed-doc-and-code cadence.

---

## 8. Session-6 architectural consolidation (2026-05-23/24)

This § is a *checkpoint*, not a decision. Session 6 opened with the
agenda "continue the entry-page build (Path B)" — the local-dev-proxy
escalation of the static chat-bubble mock shipped in Session 5. Within
a few exchanges the operator surfaced the credit-abuse concern with
running the operator's API key in user-runnable code, and the session
pivoted from build-execution to architectural reassessment. The
material below is the consolidated thinking from that pivot. It
extends §§1–7 above; where it supersedes earlier framing the
references are inline (Pattern A footnote, §4 update, "Decisions not
yet pinned" tail).

Source for §8: the Session-6 conversation transcript. Memory entries
captured separately as needed.

### 8.1 The credit-abuse forcing function

Path B as originally drafted in `project_onboarding_entry_page_plan.md`
described "a small local process [that] holds operator's Anthropic API
key, page calls localhost." The operator's reading — "as an open source
project giving any user access to all code, won't running the Claude
agent in the user's system give them free use of my credits for any
purpose they want?" — exposed that **the production architecture had
never actually been chosen**, only the dev-iteration tool had been
sketched. Path B is dev-only and safe as scoped (the key lives in the
operator's shell env, not in the repo); but the question pointed at
the deeper unanswered one: what is Path C, and how is *it* safe?

The forcing function was healthy. It revealed that committing
implementation effort to Path B as a step *toward* Path C was premature
— the production architecture wasn't picked, the credit-abuse defenses
weren't designed, and the prompt-engineering work that Path B would
have produced is portable across multiple production targets anyway.
The pivot kept the Mode-A prompt work valid as a *future* deliverable
and moved the immediate session to architectural decision-space.

### 8.2 The free-tier-API-with-visibility question (closed)

**Question**: is there any productized form of "Buzz uses Claude for
free, and the operator has visibility into Buzz's conversations"?

**Answer**: no.

- `api.anthropic.com` has no free tier. Pay-per-token from token one.
  Sign-up credits and hackathon credits exist sporadically but are
  not a sustained offer.
- `claude.ai` (consumer) has a free tier, but accounts are private to
  their owner. No API key associated, no admin visibility, no way to
  programmatically provision one for Buzz.
- Claude Team workspaces *do* give admin visibility — but at ~$30/seat/
  month per Buzz, paid by the operator. Operationally bizarre, and
  destroys the rental-bike economics that make the §4 sequencing work.
- There is no "Sign in with Anthropic" OAuth shipped by Anthropic, so
  the pattern "Buzz authenticates against his own claude.ai from your
  widget, you ride along" is closed.

The trade-space collapses to a pick-any-two-of-three over {free for
Buzz, transcript visibility for operator, free for operator}. §8.3
maps the three feasible doorways onto that trade-space.

### 8.3 The three doorways trade-table

| Doorway | Buzz pays | Operator pays | Operator sees transcripts? | Setup friction for Buzz |
|---|---|---|---|---|
| **3a — URL-redirect** (`claude.ai/new?q=...` with a pre-filled prompt pointing at an ESACP persona doc on gh-pages) | Claude free tier | $0 | ❌ No — transcript lives on Buzz's account | Lowest (one click) |
| **3b — MCP-connector** (Buzz adds an ESACP MCP server to his claude.ai) | Claude (tier TBD) | Server hosting only | Partial — only the tool-call traffic the MCP server is asked to handle, not the message-level conversation | Medium (add connector, claude.ai tier may need to be paid) |
| **2 — PWA + CF Worker** (Buzz uses chat widget on gh-pages, Worker holds operator's API key) | Nothing pre-handoff (VPS later) | API tokens, with cost-control engineering | ✅ Full — Worker is MITM and tees the stream | Lowest (just chat) |

**The Worker doorway (2) is the only one that gives the full
transcript property cleanly.** It is also the only one where the
operator pays per-token chat costs; that's the trade. The MCP path
captures partial signal; the URL-redirect captures none. Mode-A
discovery, which is the most useful traffic to capture for the
prompt-improvement flywheel (§8.6), is also tightly bounded
(~10–20 structured turns per Buzz) — which makes the Worker's
cost-control engineering tractable.

Doorways are not mutually exclusive long-term. A mature ESACP could
offer all three as separate front doors: 3a for the casually curious,
3b for users who already have claude.ai and want to integrate, 2 for
users who arrive cold. The trade-table above is for *picking the first
doorway to build*, not for picking the only one that will ever exist.

### 8.4 The Worker-tees-transcripts pipeline

When the Worker doorway is used, the Worker is a MITM between the
PWA and `api.anthropic.com`. Every request and response pair is
available for teeing. The shape:

```
PWA (gh-pages, Buzz's browser)
    │
    │  HTTPS, anonymous-with-token
    ▼
CF Worker (operator-controlled)
    ├─►  POST api.anthropic.com/v1/messages  ──►  response
    │                                              │
    │  tee (transcript, profile-so-far, headers)  │
    ▼                                              ▼
Storage backend                            (response returned to PWA)
    │
    ▼
Operator LAN box
    │  Claude curates: extract durable bits, redact PII, version
    ▼
GitHub knowledge base (commit, public repo, content-addressed by git)
```

**Choice of storage backend** (one open question): the contenders
considered and their fit —

- **CF R2** (S3-compatible, generous free tier). Simplest. Worker
  writes objects, LAN box pulls on schedule or via webhook on object
  creation. Private by default. Operationally one moving part.
  **Currently leading.**
- **Webhook over the existing WireGuard mesh** to the LAN box.
  Real-time, no intermediate storage. Reuses infra the project
  already operates (`sync_check.sh` §14 et al.). Slight reliability
  risk if the LAN box is down at write-time — would need at least
  a small Worker-side queue.
- **IPFS** (operator-floated). Technically doable via Pinata /
  web3.storage HTTP API from the Worker. Public-by-default is the
  problem — Buzz's transcripts include business-sensitive info, so
  encryption-before-pinning is required, which puts key management
  back into scope. Also: pin durability, discovery (LAN box needs
  to know which CIDs to pull), operational overhead. **Rejected as
  over-engineered for the actual use case**; the audit-trail
  property IPFS would have provided forms naturally at the git-commit
  boundary downstream anyway (git is content-addressed; the public
  repo is the immutable record).

**Privacy and consent** (transport-agnostic): capturing Buzz's
transcript at all requires an explicit disclosure on the entry page.
"We keep your conversation; curated, anonymised bits become public
training material in this repo; here's how to opt out." Without that,
the storage tech doesn't matter — the model is wrong. The disclosure
is text on the landing page, no architecture impact, but a hard
prerequisite before live capture.

### 8.5 The bridge-via-forked-repo

The operator's framing of this section, verbatim: *"the real design
'genius' has to be the shortest possible bridge between an initial
pre-canned Q & A session handled by the CF worker to ===> Buzz
installing his own Claude Code in an ESACP forked directory, where we
can pick up the conversation without being a trojan horse."*

This is a *third* handoff pattern beyond §2's Pattern A (local
installer) and Pattern B (cloud companion). It supersedes both by
removing the privileged-code-on-Buzz's-machine surface they each
required.

**Shape**:

1. PWA + Worker conduct Mode-A discovery with Buzz (~10–20 turns).
   Worker accumulates the structured profile (hardware/network/
   software/business need) + key Mode-B exchanges.
2. At handoff time, the Worker serializes the conversation state
   into a markdown file — call it `.esacp-session.md` for now —
   formatted to be readable by Claude Code as initial context.
3. Buzz is handed a short install sequence:
   *install Claude Code from Anthropic → fork ESACP onboarding repo
   → clone → run `claude` in the cloned dir.*
4. Claude Code on first invocation reads the session file (and the
   forked repo's CLAUDE.md / agent-skill scaffolding); Essex
   continues from the profile, same voice, same context. Buzz's
   first turn with Claude Code reads as continuation, not restart.

**Why this is the design genius**:

- **No Trojan horse.** The only privileged install Buzz performs is
  *Claude Code from Anthropic* — trust handoff to Anthropic, not to
  ESACP. The repo Buzz clones is *public open-source on GitHub* —
  trust handoff to GitHub. Both are trust relationships Buzz
  needs anyway if he's going to use Claude at all. No ESACP-built
  installer, no Authenticode certificate, no PowerShell
  ExecutionPolicy fight.
- **Cost cliff-down at the bridge.** The Worker only pays for the
  Mode-A phase — bounded, rate-limit-able, budget-cap-able. Past
  the bridge, Buzz's Claude subscription pays everything. The
  credit-abuse defenses (per-IP rate limit, per-session token
  budget, daily-spend circuit-breaker) only have to survive a
  bounded workload, which is engineering-tractable.
- **Conversation continuity via the filesystem, not an API.** Same
  Essex persona file used by Worker also lives in the forked repo;
  same Mode-B examples; same competence-boundary rules. Claude
  Code reading the persona file produces the *same* Essex Buzz was
  talking to in the browser. No protocol invention; markdown + git.
- **The fork is the durable artefact.** Buzz's business-specific
  configuration accumulates in his fork over time. He owns it. He
  can inspect every commit. If he wants to contribute back, normal
  open-source PR flow; if not, fine. There is no covert sync from
  his machine to ESACP's repo; the only path from his fork to
  anywhere is an explicit PR he opens. Privacy posture and open-
  source ethos line up.

**Mechanisms for the bridge itself** (decreasing convenience,
decreasing engineering complexity):

- **GitHub App + OAuth-during-Q&A**: Worker has a registered GitHub
  App. During Mode-A, Buzz OAuths it once. At handoff, Worker
  creates Buzz's fork programmatically and pushes the session
  profile as a commit at HEAD. Buzz clones, runs `claude`, profile
  is already there. Zero side-channel; everything in git from the
  start. **Cleanest end-state.** Cost: one real OAuth ask mid-Q&A
  (familiar but real).
- **Worker writes to a signed URL, Buzz fetches at install**:
  Worker writes profile to a token-scoped R2 object. Returns Buzz
  a 4-line install snippet — fork via web, clone,
  `curl <signed-url> > .esacp-session.md`, `claude`. One side
  channel (R2), expires fast, no OAuth. Cost: Buzz copy-pastes a
  multi-line snippet.
- **Worker emails Buzz the profile + instructions**: lowest-tech,
  highest-touch. Operator now has Buzz's email; Buzz has to
  context-switch to mail. Reasonable fallback for Buzzes who
  prefer email-y workflows.

**Risks worth naming honestly**:

- *Buzz must install Claude Code.* This is the load-bearing trust
  step in the whole architecture. Anthropic owns this trust ask;
  ESACP rides it but can't lower it. For the BUZZ_PERSPECTIVE
  low-tech-comfort archetype, the *install* is probably easier
  than *the terminal afterwards* — the Mode-A Q&A could include
  a "comfortable with PowerShell / Terminal?" question and route
  no-answers toward a more guided path (potentially the cloud-VM
  route from §4, where Claude Code runs on the VM and Buzz
  interacts via something more guided than a raw terminal).
- *Claude Code requires a Claude subscription.* This is now the
  single obligatory subscription pre-handoff (the VPS is post-
  handoff if §4's cloud route is chosen). Down from the operator's
  earlier "two subscriptions" worry.
- *The Mode-A → Claude-Code pickup must feel seamless.* If
  `claude` opens and Essex says "Hi, I just read your profile —
  you're the heirloom-moving operation in Eastern Ontario, you
  mentioned QuickBooks, let's start where we left off" — magic.
  If it says "Hello, how can I help?" — broken trust. Engineering:
  a small CLAUDE.md skeleton in the fork + the profile markdown is
  enough; the Mode-B Essex prompt the Worker used is reused verbatim
  in the repo so the voice is continuous.

### 8.6 The prompt-improvement flywheel

Curated Mode-A transcripts (from §8.4's pipeline) drive a feedback
loop that operates on **two axes simultaneously**:

1. **Shortening the bridge** — Mode-A becomes more efficient over
   iterations: fewer turns to reach a high-quality profile,
   conditional branches that skip questions Buzz already answered
   implicitly, better handling of "I don't know" responses, smarter
   archetype detection.
2. **Enriching the destination** — the same curated learnings update
   the CLAUDE.md / agent-skill that ships in the forked repo, the
   Mode-B example exchanges, the system prompt the post-bridge
   Buzz-Code-Essex inherits. So Buzz lands in a *better-prepared*
   Claude Code session each iteration, not just a shorter
   pre-arrival.

The flywheel is *prompt engineering driven by transcript analysis*,
**not literal model fine-tuning**. The corpus trains the operator's
prompt-writing (or the operator-with-Claude-curation's), not the
model itself. This matters because "training corpus" in §1 can
suggest fine-tuning, which is a much bigger commitment (custom model
hosting, eval pipeline, labeled data). What this architecture
actually has is faster: instant iteration, no model retraining,
every improvement ships the next session.

### 8.7 Landing-page artefacts: diagram + video

Two trust-builder artefacts the operator named as required for the
production landing page. Both must be *beautiful* in the operator's
phrasing — appealing, comforting, impressive. Both function as the
"well-lit zone" promise of §5 made *visible* before Buzz commits to
the chat.

**The diagram** is the Minecraft zone view, not the blueprint. It
shows the components Buzz is about to engage with — his machine,
his Claude Code, his cloud VPS, his domain, his SSL cert, his
Cloudflare account, his GitHub account, his Anthropic account,
ERPNext, BaRe, Cytoscape, the MCP servers — and how they fit
together. The design challenge is *legibility*: clean, sparse,
labeled, no clip-art-shadow-gradients-pretending-to-be-modern. The
kind of diagram that lands in five seconds: *"oh, that's what all
the pieces are, and they fit together like that."* If Buzz comes
away thinking "okay, someone has thought this through," the diagram
has done its job; if he comes away thinking "what fresh complexity
is this," it hasn't.

**The video** has a real maintenance commitment because provider
UIs change. Practical split:

- **One short evergreen overview** (~60–90 sec). The diagram coming
  to life, voice-over describing the zone. Brand/trust artefact.
  *No provider UIs shown* → doesn't go stale → high production
  value pays off long-term. **This is the one that needs to be
  beautiful.**
- **Per-provider deep-dive videos** (~3–5 min each). Explicitly
  versioned and dated ("Cloudflare setup, recorded 2026-Q1").
  Accepted to go stale; re-recorded annually or whenever a
  provider changes meaningfully. Lower production value; screen-
  capture + voice-over is fine.
- **The interactive setup flow itself** is the *real* tutorial.
  Either Claude-in-Chrome driving provider signups on Buzz's
  behalf, or Claude Code post-bridge guiding Buzz through them in
  plain language. The videos are *previews* of what Buzz is
  signing up for; the actual setup is automated when Buzz arrives.

**Claude-in-Chrome as setup-walkthrough method** is a fit because
the *video* shows Claude-in-Chrome doing the click-by-click. Buzz
then has three menu options for his actual setup:

- Install Claude-in-Chrome, watch it drive provider signups on his
  behalf (highest convenience, real trust ask on the extension).
- Watch the video, do it manually with the video as guide (slowest,
  lowest trust ask, works universally).
- Skip to Claude Code post-bridge and ask it for plain-language
  instructions tailored to his archetype.

The video *demonstrates* the method that's then *available* to
Buzz. Artefact and tool point at each other; that's a coherent
loop.

### 8.8 The cross-branch artefact-graduation question

The landing page Buzz actually sees lives at root `docs/` (Senior's
GitHub Pages territory). The Session-5 chat-bubble mock and the
forthcoming diagram + video work happen in `on_boarding/docs/`
(Junior's local-only Jekyll source, per the directory convention
captured in memory). At some point the on_boarding-designed
artefacts have to **graduate** to the public site.

There is no pattern for this graduation yet. It's a Senior↔Junior
coordination point per `feedback_chain_of_command_cross_branch.md`:
on_boarding produces a candidate artefact, files an issue against
main proposing the promotion, main-side Claude reviews and merges
the file into root `docs/` (with whatever site-build adjustments
the public Jekyll source needs).

This is a discipline question more than an architecture question
and is worth solving the first time an artefact is actually ready
to graduate — likely the evergreen overview video or the network
diagram, whichever lands first. Solving it before the first
artefact exists would be premature; flagging it now is the right
move.

### 8.9 Why this checkpoint is filed now, not at decision time

The session pivoted enough that the architectural picture is
materially larger than it was at Session 5 close. If this thinking
is not captured in the kit before the next context compression or
session end, it will have to be reconstructed from the transcript,
which is expensive and error-prone. The discipline is: capture the
*thinking*, defer the *decision*. §§8.1–8.8 above are thinking;
no decision is taken here. The "Decisions not yet pinned" list at
the end of §4 has been extended with the new open questions.

---

## 9. What this document is *not*

- Not a decision to build any of the above today.
- Not a commitment to any specific provider, platform, or
  architecture.
- Not a complete architecture — Stage 3 (controller-build inside
  the cloud VM or on the local box) still rests on the
  existing kit's downstream work.
- Not a substitute for the eventual operator-approved design doc.
  This is the thinking-out-loud predecessor of that doc.

When a Session-N session adopts any of the above as an objective,
it should be filed as a new agenda issue, scoped to one
component, and follow the kit's normal 1:1:1 discipline.
