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
  lightweight agent) — *can't honestly decide until iteration #1
  shows what laptop-side Essex actually needs to do*. Decision
  deferred.

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

## 8. What this document is *not*

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
