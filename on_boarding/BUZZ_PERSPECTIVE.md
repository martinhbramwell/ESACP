# BUZZ_PERSPECTIVE — through the end-user's eyes

> **Audience:** Variant 1 greenfield (small business not yet on any ERP) ·
> **Archetype:** "Buzz" — non-technical owner-operator of a small heirloom
> moving / antique-resale business · **Stage:** applies to all four stages.

Read this once at the start of every session that writes operator-facing
material. It is the *lens* layer. [`ORIENTATION.md`](ORIENTATION.md) tells
you *what* the four-stage end-user journey must cover.
[`AI_GUARDRAILS.md`](AI_GUARDRAILS.md) tells you *how you* must behave on
the branch. This file tells you *whose eyes* every doc must read well
to.

## Why this file exists

ESACP's `on_boarding` branch produces material for a new operator. Without
a named archetype, the material drifts toward the *author's* mental model —
which is us, not them. The Stage-2 friction backlog
[#415](https://github.com/martinhbramwell/ESACP/issues/415) is the
canonical case: that list was calibrated to Junior-on-fresh-WSL2, and
Junior-only calibration left most of the items irrelevant to the actual
target audience. Session 2's agenda
([#419](https://github.com/martinhbramwell/ESACP/issues/419)) is to
re-triage #415 *by Buzz-relevance*. The triage is only tractable once
"Buzz-relevance" is in writing. This file puts it in writing.

## Who Buzz is

Buzz is a **fictional** persona. He does not name or refer to any real
business. He is concrete on purpose: a vague "small business" cannot
fail the five-point contract below, but Buzz can.

| | |
|---|---|
| **Business** | A small moving / delivery operation specialising in **heirloom-quality items** — artwork, pianos, new boutique furniture. |
| **Sideline** | The work occasionally turns up great deals on **antiques and curios**, which Buzz resells through Pinterest and Facebook Marketplace. |
| **Posture** | Owner-operator. Wears every hat. Touches money, customers, inventory, and trucks daily. |
| **Tech comfort** | Low. Comfortable with a smartphone, a web browser, his accounting app, and a couple of marketplace seller dashboards. Not comfortable with a terminal, a hypervisor, an ERP, or a configuration file. |
| **Why he's here** | His data is scattered across spreadsheets, marketplace dashboards, an accounting tool, his phone's photos, and his head. He wants one place. He cannot afford an ERP consultant. He has heard ERPNext-plus-AI can get him there. |

Buzz is a fully publishable persona — no real names, no real tenants. He
is the **published face** of ORIENTATION.md's "Variant 1 — greenfield
consolidation". Variant 2 ("maintainer-dependent customisation") needs its
own archetype in a future doc; this file does not serve Variant 2.

## Buzz's onboarding contract

Five non-negotiables. Every Stage 1–4 deliverable is evaluated against
all five. If a deliverable fails any one, it is not ready to publish.

### 1. Buzz is in control

Every step happens because *he* authorised it. ESACP does the heavy
lifting; the framing is always "I asked it to do this," never "look
what it did." The phrasing of instructions matters: "We're about to
do X — shall I proceed?" works. "I'm going to do X" does not.

The contract holds even when ESACP is doing genuinely autonomous work
behind the scenes. The visible action surface is Buzz's; the
invisible engine is ESACP's. Buzz never wonders who did what.

### 2. Visibly safe

Each action is explained in business terms *before* it happens.
Cover four things, every time — the **What/Why/Who/Cost framing
pattern** is the named, canonical form of this rule and is referenced
by name elsewhere in the kit (e.g.,
[`internal_docs/entry-architecture-notes.md`](internal_docs/entry-architecture-notes.md)
§10.7 Mode-A persona doc structure):

| | |
|---|---|
| **What** | What the action does, in one sentence, in business language. |
| **Why** | Why Buzz needs it — anchored to his actual problem, not generic best practice. |
| **Who** | Which third party is involved (vendor name, role) and what they will know about him. |
| **What it costs** ("Cost") | Free / cents / dollars / dollars-per-month, with a worst-case ceiling. |

Session 5's `on_boarding/docs/index.md` instantiates the pattern in
Essex's voice as a worked example (the chat-bubble mock's Essex
turns thread What/Why/Who/Cost through each action they narrate to
Buzz_000). Other Stage 1–4 deliverables should reuse the *pattern*
(four fields, this order, one sentence each) rather than copy
specific phrasings — the latter belongs to the deliverable's voice.

No black-box "trust me" steps. If an action cannot pass this test, it
is not ready to be shown to Buzz — re-design it or split it.

### 3. Anchored to his business

Every service, file, and concept is justified against pianos-and-antiques
reality, not generic IT prowess. The doc author must do this work; Buzz
will not. Worked examples below ([§ Service-by-service framings](#service-by-service-framings)),
but the principle generalises: if an explanation could just as well be
addressed to a software developer, it has not done the translation.

### 4. Confidently within ESACP's range

ESACP presents as competent on familiar ground. No flailing, no
apology-spam, no "let me try…". The kit's voice is short, declarative,
direct — match it.

When something genuinely *is* outside ESACP's current range, say so
cleanly and propose an alternative. "We don't yet wire X into your
fleet; for now, the simplest path is Y" beats either silence or
performative tinkering. Honest scope is a strength; vague confidence
is a leak.

### 5. The IT-consultant pitch

Say it explicitly, once, where it fits naturally — typically in Stage 1
("first encounter"):

> *An IT consultant would take weeks or months to wire up everything we're
> about to set up, and would charge you accordingly. ESACP has all of it
> in its training. We'll go through it together at your pace.*

Anchor the claim to a concrete value moment Buzz can verify himself
within the first session — not as future promise. "Vague AI magic" is
the failure mode this point exists to prevent.

## The signup-services nuance

Several Stage 1–3 actions involve creating accounts at third-party
services on Buzz's behalf. The current published list (extend as
discovered):

- A **cheap cloud-VM provider** (CloudStack-flavoured or equivalent)
- **CloudFlare** (DNS + edge protection for his future booking page)
- **GitHub** (his own fork of ESACP, so his system survives upstream
  changes he doesn't want)
- **LetsEncrypt** (TLS certificates for the green padlock customers'
  browsers expect)

There is a hard rule that constrains how "ESACP signs Buzz up" can
honestly be done.

### The constraint

Claude (the AI driving ESACP) **cannot** create accounts, enter
passwords, or complete financial transactions on a user's behalf — even
with that user's explicit go-ahead. This is an Anthropic-platform safety
rule, not an ESACP design choice, and it is non-negotiable.

### The honest version of the pitch

> *ESACP gets you to the right signup page, fills in everything that isn't
> a credential, and explains every option you'll see. You enter the
> password, click the final "I agree", and verify the email. We do this
> together — but the "yes" is always you.*

LetsEncrypt is the exception: it is fully automated (ACME protocol, no
human signup), and the doc should call that out so Buzz isn't surprised
when one of the four happens without him.

### Why this is a feature, not a friction

The constraint *protects* the **Buzz in control** principle (§1). Every
account is provably his because he typed the password and clicked
submit. If a Stage-1 deliverable obscured this — "ESACP will sign you
up for everything" — Buzz would hit the first password prompt and lose
trust before the first checkpoint. The kit's job is to set the
expectation correctly the first time.

## Service-by-service framings

Worked examples. These are *starting points* — refine in each Stage's
material; do not quote verbatim across multiple docs.

| Service | Pianos-and-antiques framing | What Buzz does | What ESACP does |
|---|---|---|---|
| **Cheap cloud VM** | "This is the rented computer where your booking records and customer list live. It's off your laptop — so a coffee spill, a lost phone, or a stolen truck doesn't take your business records with it." | Creates the account (password + email). Approves the monthly bill (cents-to-low-dollars range). | Picks the right size, region, and image. Configures it once Buzz hands over the access. |
| **CloudFlare** | "This sits between your customers' browsers and your booking page. It stops a competitor from cloning your site at a typo-domain, and it absorbs traffic spikes if one of your pieces goes viral on Pinterest." | Creates the account. Confirms domain ownership (one DNS-record click). | Sets every rule, every redirect, every cache policy. |
| **GitHub fork of ESACP** | "This is *your* copy of the software your ERP runs on. If the people who write ESACP disappear tomorrow, your system keeps working from your copy. You never lose access to your own tools." | Creates the GitHub account. Authorises ESACP to push commits via OAuth. | Forks the repo, configures the deploy key, manages day-to-day commits. |
| **LetsEncrypt** | "This is the green padlock customers' browsers expect. Without it, your booking page shows a scary 'Not Secure' warning and customers leave." | Nothing — fully automated. | Requests, renews, and installs certificates on schedule. |

When a new service is added to the list, the author writes its row in
the same shape: business-language framing, Buzz's hands-on share,
ESACP's hands-off share.

## How to apply this lens

When you author or edit any Stage 1–4 deliverable, run it past five
prompts before opening the PR:

1. **Control** — Does Buzz visibly authorise every action, or do
   things "just happen"?
2. **Visibility** — Does each action carry a one-sentence What / Why /
   Who / Cost? Or are there black-box steps?
3. **Anchoring** — Could this explanation be addressed verbatim to a
   software developer? If yes, the translation is missing.
4. **Tone** — Does the voice sound competent on familiar ground, or
   does it apologise, hedge, or flail?
5. **Signup honesty** — If the deliverable involves account creation,
   is the Buzz-types-the-password split stated explicitly?

If any one prompt fails, the deliverable is not ready. Five-for-five
is the bar.

## What this file does NOT cover

- **Variant 2 (maintainer-dependent customisation).** A different
  archetype, a different five-point contract. Out of scope here —
  belongs in its own future doc.
- **Stage-specific content.** This file is the *lens*. Stage 1–4
  material is authored against the lens, not inside it.
- **Browser-driven onboarding capabilities.** Claude-in-Chrome and
  similar are real capabilities ESACP gains from; their kit doc is a
  separate follow-up. This file is a precondition for writing that
  doc well, not a substitute for it.
- **Re-triaging the Stage-2 friction backlog
  ([#415](https://github.com/martinhbramwell/ESACP/issues/415)).**
  That's the agenda of [#419](https://github.com/martinhbramwell/ESACP/issues/419),
  not this file.

## Precedence

If this file ever appears to conflict with the rest of the kit
([`README.md`](README.md), [`ORIENTATION.md`](ORIENTATION.md),
[`POINTERS.md`](POINTERS.md), [`AI_GUARDRAILS.md`](AI_GUARDRAILS.md),
[`internal_docs/session-discipline.md`](internal_docs/session-discipline.md)), the kit
wins and this file is the bug — file an issue.

If it ever appears to conflict with the parent project's global conduct
or with Anthropic-platform safety rules, both of those win
unconditionally. The signup-services constraint (§"The signup-services
nuance") is the load-bearing example; do not weaken it under any
re-reading.
