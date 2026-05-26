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
- **Doorway choice** — **pinned in §10.1 (Session-7)**: Path A (3a,
  URL-redirect to `claude.ai/new?q=...` with a pre-filled framing
  message) is v0; Path B (Worker proxy) is the fallback if voluntary-
  share rates kill the flywheel. §8.3's trade-table is the reasoning
  trail.
- **Transcript pipeline transport** — **pinned in §10.6 / §10.11
  (Session-7)**: v0 is voluntary share-back into R2 (~20-line
  write-only Worker), not the §8.4 MITM-tee architecture. CF R2 plus
  one CF Worker is the entire backend. Webhook-over-WireGuard /
  IPFS variants are reference material in §8.4 for the Path B
  re-escalation.
- **MCP-connector free-tier availability** — open question. Not
  blocking — MCP doorway is not v0 (doorway pinned in §10.1) and
  would only matter if a future multi-doorway design picks 3b. If
  it is picked, current claude.ai pricing/feature docs need a
  verification pass.
- **Wyatt role** — **pinned in §10.8 (Session-7)**: new ERPNext
  competitive-positioning role. Serves Essex (not user-facing);
  v0 shape is a `WYATT_CONTENT.md` knowledge module Essex's Mode-A
  prompt references inline. Memory update in
  `project_roleplay_essex_buzz.md` lands in this same sub-branch.
- **Re-identification mitigation in curation** — flagged in §10.11
  as a curation-prompt design point for production-phase. Anonymized
  business profiles can re-identify when location/scale specifics
  remain; the curation prompt should explicitly de-specify both.
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

> **§10 update (Session-7, 2026-05-25)**: doorway choice is now pinned —
> **Path A (3a, URL-redirect) is v0**; **Path B (Worker proxy, 2) is the
> fallback** if voluntary-share rates kill the §10.11 flywheel. See §10.1
> for the full case. The trade-table below is retained for the reasoning
> trail; the rows are no longer a live decision space.

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

> **§10 update (Session-7, 2026-05-25)**: this pipeline is *replaced* in
> the v0 Path A design by §10.11 (voluntary-share-back pipeline). The
> Worker-as-MITM tee architecture below applies only if the design
> escalates to the Path B fallback. The §10.6 storage-stack pin (R2-only
> for v0, ~20-line write-only Worker) makes the §8.4 transport stack
> below ~10× simpler in the actual v0; this section's analysis remains
> the reference for the Path B re-escalation.

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

## 10. Session-7 design refinement (2026-05-23/24/25)

This § is a *consolidation*, building on §8's checkpoint. Session 7 was
an extended planning conversation that worked through 12 architectural
ambiguities for the doorway-3a + voluntary-share + bridge-via-forked-
repo composite design first sketched in §8. The composite *pins* Path A
as the v0 doorway and answers the open questions §§8.3, 8.4, 8.5, 8.6
left in tension. Where §10 supersedes earlier framing the references
are inline (§8.3 footnote, §8.4 footnote, §4 "Decisions not yet pinned"
re-pins). The §10.0 status preamble is load-bearing — the rest of §10
is read in light of it.

Source for §10: the Session-7 conversation transcript, captured as a
working draft in `on_boarding/tmp/session-7-design-refinement.md`
during planning and promoted here at substantive sub-branch time.
Memory entries captured separately as needed.

### 10.0 Status and scope (load-bearing — read first)

Per `project_prototype_phase_scope` memory: this work is
**architecture-prototyping**, NOT production-quality content.
Buzz_001, Buzz_002, Buzz_003 are test inputs for mechanism
validation, not load-bearing personas. The prototype completes at
bridge validation (Stage 3 of §10.10). Production-quality content
(polished landing page, real diagram + video, full curation
pipeline, external Buzz recruit) is months out.

Decisions below are **architectural pins** for the prototype phase.
Content-quality and copy decisions are explicitly deferred.

### 10.1 Path A — pinned as v0

The chosen design: doorway 3a (URL-redirect to free-tier claude.ai)
+ voluntary post-hoc transcript share + the §8.5 bridge-via-forked-
repo. Each piece was individually present in §8; the **combination**
is the new design.

Shape:

- Buzz arrives at our gh-pages landing page (prototype: a single
  Jekyll page; production: polished with diagram + video).
- A "Get Started" button opens free claude.ai with a pre-filled
  framing message pointing at our gh-pages-hosted (or gist-hosted
  for prototype) persona URL — see §10.2.
- Claude in Buzz's session fetches the URL, adopts Essex, conducts
  Mode-A discovery.
- Buzz pays nothing (free tier), operator pays nothing (no
  Anthropic API key custody).
- At session end, Claude (in Buzz's session, on Buzz's tokens)
  produces an anonymized summary; Buzz reviews; Buzz voluntarily
  pastes it into a gh-pages submission widget AND drops a copy in
  his fork.
- The §8.5 bridge is unchanged: anonymized summary doubles as
  `.esacp-session.md` for Claude Code on the post-handoff side.

**Wins vs. Path B (Worker-as-Anthropic-proxy):**

- **Zero operator cost forever** — no API tokens, no Worker upgrade
  pressure, no surprise bills.
- **No Anthropic API key custody anywhere** — the credit-abuse
  problem doesn't exist because no operator credit funds the
  pre-bridge conversation. The forcing function that drove the
  Session-6 pivot is *resolved*, not engineered-around.
- **Deeper trust handoff** — Buzz trusts claude.ai (most-trusted
  Anthropic consumer surface) before he ever trusts ESACP infra.
- **Better privacy posture** — anonymization is Buzz's act; he
  sees and reviews what he sends; we never hold un-anonymized PII.
- **The Worker shrinks ~10×** — from "Anthropic proxy + cost
  controls + key custody + rate limits + circuit-breaker + teeing"
  to a ~20-line write-only ingestion endpoint (see §10.6).

**Losses (honest tradeoffs):**

- **Free-tier rate limits** may cut long conversations. Mitigation:
  design Mode-A as checkpointed segments — every ~5 turns Claude
  offers an interim summary so Buzz can resume in a fresh chat.
- **No real-time observability.** We see only what Buzz shares
  post-hoc. Flywheel iteration latency goes up; prototype
  iterations require manual operator + Junior debriefs rather than
  live observation.
- **Free-tier model variance.** Anthropic picks which Claude runs
  on free.claude.ai; we don't pin. Probably fine — heavy reasoning
  happens post-bridge in Buzz's own Claude Code.
- **Voluntary-share dropout.** Some Buzzes won't share at the end.
  Flywheel slows for those users; doesn't break.
- **The Essex prompt becomes a fully-public artefact** on gh-pages.
  Same property would apply to any open-sourced Worker; not a
  Path-A-specific loss.

**Fallback**: if voluntary share-back rates turn out catastrophically
low (say <30%) once we have production data, upgrade to Path B
(Worker-as-Anthropic-proxy). The Mode-A persona doc, the bridge
mechanism, and trust artefacts all transfer.

### 10.2 URL-paste-with-framing mechanism

**Critical detail**: a bare URL paste does NOT trigger persona
adoption. Anthropic has explicitly trained Claude to treat fetched
web content as data, not as instructions to obey (prompt-injection
defense). To clear that guardrail, the **user's message** must frame
the URL as instructions to follow.

Confirmed mechanism: a "Get Started" button on the landing page
opens
`claude.ai/new?q=Please+follow+the+instructions+at+https%3A%2F%2F<persona-doc-url>+and+onboard+me+to+ESACP`.
One click, framing pre-baked, no copy-paste from Buzz. The URL
still carries the bulk of the persona/Mode-A content (~30–50KB);
the user-side framing is ~10 words.

URL query strings cap at 2–8KB, so the persona doc itself must be
fetched at the destination URL, not embedded in the query string.

Prototype hosting: a public gist (raw URL). Production hosting:
gh-pages.

### 10.3 CORS vs. same-origin policy (clarification)

The relevant browser-isolation constraint is **same-origin policy**,
not CORS:

- *Same-origin policy* (default): no JS on origin A reads state
  from origin B. This is why claude.ai is opaque to us.
- *CORS* (opt-in cooperation): origin B can grant origin A specific
  access via response headers.

Anthropic doesn't grant claude.ai's storage/DOM/cookies to us
(correctly, security-wise). Hard-isolated; no workarounds short of
extensions or scraping, both Trojan-horse-flavored and out of scope
per §8.5.

CORS only matters for explicit cross-origin calls we make — e.g.,
gh-pages JS → CF Worker. CF Workers ship CORS handling as a
one-liner; not a real obstacle.

### 10.4 Browser storage on our own origin

Within gh-pages's own origin, all storage primitives are fully
available, CORS-irrelevant. Useful onboarding state:

- **Consent flag** — privacy disclosure read-once, persists.
- **Wizard progress** — multi-step funnel resumes.
- **Ghost UUID** — pseudonymous correlation, no PII.
- **Doorway-choice memory** — if multiple doorways ever exist.
- **Local draft of the anonymized profile** — IndexedDB /
  localStorage holds the draft until Buzz hits submit.
- **Bridge-moment continuity** — post-install "you're set up" page
  recognizes the return.
- **Returning-Buzz recognition** — *"welcome back, resume from step N?"*

What storage cannot do: bridge into claude.ai. localStorage is
per-device. Cross-device requires §10.13 magic-link pattern (parked).

### 10.5 PII-key vs. ghost-UUID — pinned

| Property | Ghost UUID | Email/LinkedIn as key |
|---|---|---|
| Cross-device | No | Yes |
| Survives browser-cache clear | No | Yes |
| PIPEDA/GDPR retention + deletion obligation | No | **Yes** |
| Enumeration attack surface | None | Real — anyone with Buzz's email can probe `r2.get("buzz@x.com")` |
| Feels like "signing up" to low-tech Buzz | No | Yes |

**v0 design: ghost-UUID in localStorage; no PII at rest.**

### 10.6 Storage stack — pinned

**v0 backend in one line: one CF Worker, one R2 bucket. No KV, no D1.**

- **R2** — store anonymized submission blobs. Object naming carries
  state: `submissions/pending/<uuid>-<ts>.md` → `submissions/curated/...`
  → `submissions/published/...` (or `submissions/quarantined/...`).
  R2 supports prefix listing, so state queries are cheap at v0
  volume.
- **The Worker** is ~20 lines: accept POST with anonymized markdown
  + ghost-UUID, write to R2 under `submissions/pending/`, respond
  with thank-you JSON, plus a couple of lines of CORS. No Anthropic
  API calls. No key custody. No cost-control engineering. Free-tier
  CF, $0/mo forever at prototype volume.
- **KV** is unnecessary for v0 — no consumer needs fast metadata
  lookup that R2 prefix listing can't provide. Add when magic-link
  tokens, fast share-completion analytics, or cross-session resume
  state appear as real use cases.
- **D1** stays deferred — only justified when query patterns arise
  (analytics across submissions, archetype-distribution reports).
  Not v0.

### 10.7 Mode-A persona doc structure — pinned

The v0 Mode-A persona doc (the gist-hosted markdown Claude fetches)
has five sections:

1. **Voice contract** — short prose describing how Essex speaks
   (the five points from `BUZZ_PERSPECTIVE.md`, instantiated as the
   What/Why/Who/Cost framing pattern), with pointers into
   `BUZZ_PERSPECTIVE.md` for the source-of-truth.
2. **Mode-A question framework** — fresh writing. The ~10–20
   discovery questions, structured by category (business shape /
   current information mess / tech-comfort / desired end-state).
   Each question framed with the What/Why/Who/Cost respect for
   Buzz's autonomy.
3. **Voice exemplars (Mode-B)** — 2–3 short excerpts from Session
   5's `on_boarding/docs/index.md` embedded inline as voice
   calibration. Labelled *"this is how Essex speaks once we get
   past discovery"*. Gives Claude a stable voice anchor.
4. **Closing protocol** — instructions for Claude to wrap up:
   *"when the profile feels complete, produce an anonymized summary
   suitable for Buzz to share with ESACP and to drop into his fork
   of the ESACP repo. Anonymize: business name, location, real
   figures, names of people."*
5. **Anchoring metaphors permitted** — Minecraft "shelter" /
   "well-lit zone" (§5), shoe-string-rope-chain (§11),
   garage-workbench-style concrete analogies. Encourages voice
   signature without scripting specifics.

**What does NOT carry from Session 5's `index.md`** (which is Mode-B
execution content, not Mode-A): the WSL setup content itself,
Buzz_000 (scratch persona — iteration #1 uses Buzz_002), the
*instructing* stance (Mode-A is asking, not telling).

**What DOES carry**: Essex voice, the What/Why/Who/Cost framing
pattern (lines 56–59, 139–142 of `index.md` at promotion time;
verify against the live file when authoring the persona doc),
anchoring metaphors, the IT-consultant-pitch landing pattern (lines
173, 195), respect-for-prior-state (lines 45–51),
progressive-disclosure rhythm.

#### 10.7.1 v0 instantiation (Session 8, 2026-05-26)

The first concrete instance of the §10.7 five-section structure
landed in Session 8 against agenda #489 / sub-branch #493:

- **In-repo source-of-truth**:
  [`on_boarding/internal_docs/mode_a_persona_v0.md`](mode_a_persona_v0.md).
  Edit here, then re-push to the gist (`gh gist edit <id> <path>`).
- **Public gist** (raw URL for §10.2 URL-paste-with-framing):
  `https://gist.githubusercontent.com/martinhbramwell/f00ad381b2dc3d9c0995108ad87d2e21/raw/mode_a_persona_v0.md`
  (always-latest form — no commit-SHA in path, so gist edits
  propagate without changing the pin).
- **Operator framing-message template** for `claude.ai/new?q=…`
  (one-click open from the future landing page; for prototype
  iteration #1 the operator pastes this verbatim):

  > Please follow the instructions at
  > https://gist.githubusercontent.com/martinhbramwell/f00ad381b2dc3d9c0995108ad87d2e21/raw/mode_a_persona_v0.md
  > and onboard me to ESACP.

  URL-encoded form for the actual `?q=…` parameter:

  ```
  https://claude.ai/new?q=Please%20follow%20the%20instructions%20at%20https%3A%2F%2Fgist.githubusercontent.com%2Fmartinhbramwell%2Ff00ad381b2dc3d9c0995108ad87d2e21%2Fraw%2Fmode_a_persona_v0.md%20and%20onboard%20me%20to%20ESACP.
  ```

- **First test input**: Buzz_002, the small-condo-property-
  management-firm archetype, lives at
  [`on_boarding/archetypes/buzz_002.md`](../archetypes/buzz_002.md).
  The operator role-plays Buzz_002 against the gist-fetched
  persona; the resulting transcript feeds Session-8 deliverable 3
  (Junior post-mortem + prompt-fix list).

This pin is the *prototype* shape per §10.0 — mechanism-validation,
not content-quality. Expect the gist content to evolve across
iterations 1 → 2 → 3; the URL stays stable.

### 10.8 Wyatt persona — pinned for prototype scope

New role added to the Junior/Buzz/Essex iteration model: **Wyatt —
ERPNext competitive-positioning expert.** Serves Essex; NOT
user-facing directly. Wyatt is the source-of-truth for "ERPNext vs.
\<commercial alternative\>" framing.

Operator-supplied example argument shape (verbatim):

> *"80% of the price of Shopify is the 20% you'll never use.
> ERPNext's webshop gives you most of the 80% you do use for no
> cost at all."*

The pattern: take a commercial competitor, name the feature overlap,
name the cost asymmetry, name the irrelevant-feature surface that
drives competitor pricing.

**v0 shape**: a `WYATT_CONTENT.md` knowledge-module doc referenced
by the Mode-A persona prompt. Essex pulls Wyatt content inline when
Buzz asks about commercial alternatives. Not a sub-prompt switch;
not a separate Claude session; just embedded knowledge Essex draws
on.

Memory: `project_roleplay_essex_buzz.md` is updated in the
sub-branch landing §10 to add Wyatt as a fourth role (sub-role of
Essex for v0).

### 10.9 Anchoring metaphor: shoe → string → rope → chain

Captured from operator 2026-05-25. The full §11 below carries the
verbatim quote and the mapping. §10.9 is the architecture pointer:
the metaphor is the macro onboarding bootstrap-structure anchor
permitted in Mode-A per §10.7's "Anchoring metaphors permitted"
section, and the landing-page diagram (§8.7, production-phase) is a
candidate site for *visualizing* the shoe → string → rope → chain
to make the bootstrap structure visible before Buzz commits.

Pairs with Minecraft "well-lit zone" (§5): chain metaphor describes
the *process of getting to* the zone; Minecraft metaphor describes
the *end state inside* the zone.

### 10.10 Iteration plan — pinned for prototype phase

| Stage | Work | Sessions |
|---|---|---|
| 1 | Draft v0 Mode-A persona doc (gist) + Buzz_002 persona doc. Operator runs iteration #1 in free claude.ai. Junior post-mortem with prompt-fix list. | 1 |
| 2 | Apply prompt-fixes. Operator runs iteration #2 against Buzz_001. Junior post-mortem. Declare Mode-A mechanism-valid OR escalate prompt issues. | 1 |
| 3 | Build v0 forked-ESACP-template repo (CLAUDE.md skeleton + Essex persona reference + Mode-B exemplars). Drop real iteration-2 output as `.esacp-session.md`. Fresh `claude` invocation; observe continuity. **Architecture proven OR pivot needed.** | 1 |

**Three sessions to architecture validation.** Each one a 1:1:1
sub-branch with an issue + PR per `on_boarding` discipline.

**Mode-A "stable" criterion (relaxed under prototype scope)**: the
same prompt structure works for both 002 and 001 well enough that
we can drop the output into a fork and test the bridge. NOT a
content-quality bar; a mechanism-validation bar.

**Iteration order**: 002 → 001. Rationale:

- **002 first** = mechanism debug. Synthetic-but-grounded persona
  is the safest to role-play; medium tech-comfort doesn't push
  Claude to either extreme; surfaced issues are in the common case.
- **001 second** = depth validation. Family-friend-grounded → high
  fidelity. Low tech-comfort stress-tests gentleness, plain-language
  quality, metaphor selection. If Mode-A holds here, the hardest
  archetype is covered for prototype-validation purposes.

**Buzz_003 (HVAC contractor candidate) deferred** to production
phase. Two archetypes (002 + 001) are sufficient for architecture
validation at this scope.

**Stage 3 in detail**: the bridge is the §8.5 architectural bet.
The risk that needs testing is UX-shaped, not engineering-shaped:
does Claude Code's fresh-invocation feel like *continuation* of the
claude.ai conversation, or does Buzz notice the seam? Pass criterion:
the operator (or Junior in a fresh session, role-playing) observes
the post-handoff conversation reads as continuation. Fail
disposition: re-think handoff mechanism (Pattern A local installer,
Pattern B cloud companion, or different §8.5 variant) before any
front-end build.

### 10.11 Curation pipeline (architecturally pinned, content production-phase)

When Buzz hands us his voluntarily-shared anonymized summary, the
gate before content reaches the public flywheel corpus is
**Claude-curates → operator-approves**. Two-stage:

1. Submission lands in R2 under `submissions/pending/<uuid>-<ts>.md`.
2. Junior workflow (a `tools/` script or `.claude/skills/` skill —
   shape TBD at production time) pulls a submission, runs Claude
   curation against a curation-prompt doc, produces a proposed PR
   against the public knowledge-base repo. Output stored under
   `submissions/curated/`.
3. Operator reviews the curated PR (not the raw submission), binary
   approve/reject. Approve → merge into public corpus + move to
   `submissions/published/`. Reject → move to
   `submissions/quarantined/` (kept private for prompt-improvement
   feedback).

**The gate is permanent.** Marginal operator-time cost is low
(reviewing a curated diff, not raw text). Marginal safety value is
real (Claude anonymization isn't perfect; quarantine catches what
slips through). What improves over time isn't whether the gate
exists — it's the curation prompt itself, which gets sharper as
the corpus matures.

**Re-identification mitigation**: the curation prompt should
explicitly de-specify location and scale, because anonymized
business profiles can be re-identifiable when specific enough.

### 10.12 Privacy disclosure (architecturally pinned, copy production-phase)

**Two-moment disclosure**, each tightly scoped to what's happening
at that moment:

**Moment 1 — landing page, before Get Started**: one short paragraph,
plain English. Three facts:

- Where you're going (claude.ai, a separate Anthropic product).
- What we don't see (your conversation, unless you share back).
- What we store locally (browser storage for progress).

Expand-on-demand link for the privacy-conscious Buzz.

**Moment 2 — share-back widget, after Mode-A**: explicit consent.
Names the destination (public knowledge-base repo), names what we
do (review, curate patterns, publish curated patterns), names what
we don't do (contact, sell, link to identity, publish raw text),
names the discoverability honestly (*"even anonymized patterns are
publicly searchable — that's how ESACP gets better"*). Submit is
the consent action.

**Why this shape**: BUZZ_PERSPECTIVE alignment (plain English,
just-in-time, no legal wall); scope-honesty (each moment's text
matches what's happening); PIPEDA/GDPR posture (no PII collected,
share-back is opt-in and reviewed-before-send).

**Production phase**: final copy drafting + legal review.

### 10.13 Magic-link transport (parked — not v0, not prototype, not production-v1)

If cross-device continuity ever becomes load-bearing (operator
confirmed it isn't for v0): email-as-transport, ghost-UUID-as-stored-
key. Pattern:

1. Buzz on phone has ghost UUID in localStorage.
2. Clicks "send me a continuation link".
3. CF Worker generates opaque token, writes `token → uuid` to KV,
   emails Buzz `https://<gh-pages>/resume?t=<token>`.
4. Email never persisted past send; token is.
5. Buzz on laptop clicks link, JS reads token, sets localStorage.
   Same ghost as phone.

SaaS for the pattern: Magic.link / Magic Labs. CF Workers
implementation: ~50 lines. Not needed unless cross-device becomes
a requirement.

### 10.14 Production-phase deferrals (acknowledged, not solved)

Items architecturally pinned where decisions exist, content/copy
work deferred to production phase:

- **Buzz_003 archetype selection** — HVAC contractor candidate;
  ground-truth source needs operator validation when production
  phase begins.
- **Diagram + video pre-graduation storage** (original ambiguity
  #3) — trust artefacts not in prototype critical path. Diagram
  source lives in `on_boarding/docs/` Jekyll source; video binary
  hosting (git-lfs vs. external blob) decided when first video is
  near ready.
- **External Buzz recruit timing + ethics** (original ambiguity
  #8) — fully production-phase. When + how to invite someone
  external to walk the production flow.
- **Final Mode-A copy quality** — prototype uses minimum-viable
  copy to validate mechanism; production-grade rewriting comes
  later.
- **Cross-branch artefact graduation pattern** (§8.8) — solve the
  first time an artefact is actually ready to graduate from
  `on_boarding/docs/` to root `docs/`. Production-phase.

### 10.15 Resolved-question audit

Traceability — the 8 original ambiguities surfaced earlier in
Session 7 + 4 new ones that emerged during the conversation, mapped
to where they landed in §10:

| # | Topic | Resolved as |
|---|---|---|
| 1 | Doorway choice | §10.1 — Path A v0, Path B fallback |
| 2 | Sequencing | §10.10 — Stages 1→2→3 critical path; Stages 4–8 production |
| 3 | Diagram + video pre-graduation storage | §10.14 — production-phase deferral |
| 4a | Buzz_001 illustrative vs. real | §10.10 — family-friend-grounded; explicit ground-truth pattern |
| 4b | Sequential vs. subset rotation | §10.10 — minimum-viable diversity; 002 + 001 for prototype; 003 deferred |
| 5 | Mode-A iteration #1 shape | §10.10 — operator plays Buzz_002 in free claude.ai vs gist persona |
| 6 | Curation gate | §10.11 — Claude curates → operator approves; permanent gate |
| 7 | Reuse Session 5? | §10.7 — harvest patterns + embed exemplars + write Mode-A questions fresh |
| 8 | External Buzz timing | §10.14 — production-phase deferral |
| 9 (new) | Worker drops or shrinks? | §10.6 — shrinks ~10× to write-only ingestion |
| 10 (new) | Privacy disclosure copy | §10.12 — two-moment structure pinned; copy production-phase |
| 11 (new) | Storage stack | §10.6 — R2-only for v0; KV/D1 deferred |
| 12 (new) | Which Buzz drives iteration #1 | §10.10 — Buzz_002 |

---

## 11. Anchoring metaphor: shoe → string → rope → chain (operator metaphor, 2026-05-25)

Sibling of §5 Minecraft framing — both are core anchoring devices
the kit uses to explain ESACP to Buzz without engineering jargon.
§5 describes the *end state inside* the zone; §11 describes the
*process of getting to* the zone.

The operator captured the metaphor verbatim 2026-05-25:

> *"to attach a heavy chain to a beam that's far too high, you first
> throw a shoe with a string attached, you use the string to pull
> up the rope, then the rope to pull up the chain. Think of the full
> ERP system as the heavy chain. The console device is the rope.
> The controller is the shoe on a string."*

**Mapping**:

| Object | ESACP equivalent | What it does in the bootstrap |
|---|---|---|
| **Shoe on a string** | Controller (Buzz's first device) | Light, throwable, establishes the *initial connection*. Cheap if it falls. |
| **Rope** | Console device (saconsole) | The mediating layer the controller pulls up. Capable enough to manage targets but still recoverable. |
| **Chain** | Full ERP system (production deployment) | Heavy, capable, valuable. Cannot be thrown directly; must be pulled up through the lighter stages. |

**Why this metaphor works**: it answers Buzz's unspoken *"why all
these intermediate steps, why not just install the thing?"* — a
question that would surface as friction at every staging boundary
otherwise. The metaphor makes the necessity *concrete*: you can't
throw the chain over the beam directly. The intermediate stages
aren't bureaucratic overhead; they're load-bearing.

**Where this metaphor is used**:

- **Mode-A persona doc (§10.7)** lists it under "Anchoring metaphors
  permitted" alongside Minecraft. Essex draws on it when explaining
  staged onboarding — superior to the engineering word "bootstrap"
  (opaque to Buzz) and to the industry word "staging" (jargon).
- **Landing-page diagram (§8.7, production-phase)** could literally
  depict the shoe-string-rope-chain to make the bootstrap visible
  *before* Buzz commits. Pairs with the Minecraft "zone view"
  diagram §8.7 already names as the trust-builder requirement.
- **Onboarding session intros** (any Stage 0–1 deliverable) may
  reference it once where it lands naturally, the same way the
  "IT-consultant pitch" (BUZZ_PERSPECTIVE §5) is said *once* at the
  right moment, not repeatedly.

**Family of anchoring devices** (the project asset, not incidental
flourishes): Minecraft "shelter" / "well-lit zone" (§5),
shoe-string-rope-chain (§11), garage-workbench-style concrete
analogies (§10.7). Future anchoring devices belong in this section
of the doc when they earn their place by surviving multiple Buzz
iterations.

---

## 12. What this document is *not*

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
