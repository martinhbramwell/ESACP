# Buzz_002 — Small condo-property-management firm

> **Audience:** Variant 1 greenfield (small business not yet on any ERP) ·
> **Archetype:** owner-operator of a small property-management firm
> serving a portfolio of condominium associations ·
> **Stage:** prototype-phase test input for §10.10 iteration #1.

This file is one of the kit's named archetype profiles, sibling to
the Variant-1-default persona in [`../BUZZ_PERSPECTIVE.md`](../BUZZ_PERSPECTIVE.md).
The BUZZ_PERSPECTIVE five-point contract still applies; this file
specialises the *information shape, symptom set, and tech-comfort
calibration* for the condo-property-management archetype so Essex
can recognise the case during Mode-A discovery and so the operator
can role-play it consistently in iteration #1.

## Prototype-phase scope

Per `project_prototype_phase_scope` memory: Buzz_002 is a
**test input for mechanism validation**, not a load-bearing persona.
The profile is grounded enough to drive a realistic Mode-A
conversation; it is not a real client and is not pinned for
production. Production-phase archetype work (real-recruit timing,
ethics, ground-truth validation) is in §10.14 of
[`../internal_docs/entry-architecture-notes.md`](../internal_docs/entry-architecture-notes.md).

## Who Buzz_002 is

| | |
|---|---|
| **Business** | A small Ontario property-management firm contracted by 5–50 condominium corporations to handle the day-to-day operations the volunteer boards can't. |
| **Headcount** | 2–25 people. Owner-operator + a property manager or two + part-time bookkeeping + a front-desk / dispatch role. Big enough to need delegation, small enough that *everyone knows everyone's files*. |
| **Posture** | Owner manages the firm and personally carries 2–4 of the larger or trickier accounts. Reads every condo board's meeting minutes. Signs every vendor contract above a threshold. Wears the compliance hat across all associations. |
| **Tech comfort** | Medium. Owner is fluent in Outlook, Excel, QuickBooks, and one property-management SaaS that does *half* of what's needed. Comfortable with web logins and multi-tab browsing. Not comfortable with a terminal, SQL, or a server. Has tried to centralise data twice and abandoned both attempts. |
| **Why they're here** | Spreadsheets and email don't scale past ~15 associations. Staff turnover is expensive because institutional knowledge lives in whoever last touched the file. Every annual compliance review exposes the same sprawl. They want one place for everything *per association*, with the firm-wide view sitting above it. |

## Information complexity (the part that distinguishes Buzz_002)

Each managed condo corporation carries its own:

- **Governing documents** — declaration, bylaws, rules,
  amendments. Different per association. Buzz_002 must produce the
  current version on demand for owner inquiries, board questions,
  and resale lawyers.
- **Meeting cycle** — AGMs (annual), SGMs (special), board meetings
  (monthly-ish). Each meeting generates an agenda, packet,
  attendance + proxy register, vote record, and minutes. Vote
  tracking has *quorum* and *proxy* logic the staff currently does
  by hand.
- **Financial statements** — operating budget, reserve fund,
  arrears report, annual audit. Often one QuickBooks file *per
  association* — the firm has 5–50 QuickBooks files.
- **Vendor coordination** — plumber, electrician, snow removal,
  landscaping, elevator maintenance, fire-safety inspection, HVAC.
  Mostly the same vendor pool across associations but priced and
  contracted per-association. Invoice routing varies — some
  associations require board pre-approval, some delegate to the
  property manager up to a threshold.
- **Preventative maintenance schedules** — fire-alarm tests,
  elevator inspections, backflow-prevention certifications,
  reserve-fund-study refreshes. Compliance-driven; auditable.
- **Unit-owner communications** — request intake, complaint
  resolution, notice distribution (AGM notice, rule changes, fee
  increases). Status tracking happens in flagged Outlook emails.
- **Ontario Condominium Act compliance** — the legal floor.
  Reserve-fund studies, AGM-notice windows, status-certificate
  turnaround. Penalties are real. The firm-wide compliance posture
  is the owner's responsibility across every association.

## Symptom set (what Essex should recognise during Mode-A)

These are the concrete pain points Essex should expect to surface
when asking about the current information mess. They are *what
Buzz_002 will describe in their own words* — Essex should not
volunteer the diagnosis until Buzz has named it.

- **"Where is X?" → three-email triage**. Asked about an
  elevator-maintenance contract; Joanne thinks Karen filed it; two
  more emails to confirm. Multiply by the ~50 documents the firm
  routinely produces per association.
- **AGM-packet preparation takes 3 days** because financials,
  reserve-fund snapshot, manager's report, and the agenda all live
  in different tools and have to be hand-collated into a single PDF.
- **Vendor invoice approval is per-association ad-hoc**. Some
  go through the manager, some through the board chair, some get
  paid then approved. Audit findings repeat year over year.
- **Unit-owner complaints tracked in flagged Outlook emails**. A
  complaint marked "in progress" by someone who has since left the
  firm is invisible to whoever inherits the account.
- **Bylaw lookups end at the wrong version**. Amendments live in
  scanned PDFs in someone's email; the active version is not
  authoritative anywhere central.
- **Staff onboarding takes 3 months** because so much knowledge is
  in heads, not in files.
- **The QuickBooks fleet is a maintenance burden**. Year-end
  involves 5–50 separate close cycles. Cross-association reporting
  (e.g., firm-wide arrears posture) doesn't exist; the owner
  recalculates by hand.

## Tech-comfort calibration

What Essex can assume Buzz_002 will handle without hand-holding:

- A web browser, multiple tabs, logging in to several services per
  day.
- Excel — pivot tables, VLOOKUPs at a stretch, comfortable with
  formulas the bookkeeper set up.
- QuickBooks (Desktop or Online; they likely use whichever they
  started with and resist switching).
- One property-management SaaS partially adopted (Buildium /
  Yardi Breeze / Condo Manager — variants of the same category).
- Email-as-workflow muscle memory. Outlook flags, folders, rules.

What Essex must **not** assume:

- A terminal or command line. Never opened one.
- Anything resembling a server, a hypervisor, a container, or a
  database administration tool. Words like "instance", "schema",
  "deployment" land as alien.
- Comfort with version control, even for documents. Track-changes
  in Word is the ceiling.
- Patience for setup ceremony. Two prior centralisation attempts
  failed because *the setup took longer than the value showed up*.

The handoff metaphor that lands well with Buzz_002: a *new office
assistant who already knows every file* — not a new piece of
software they have to learn from scratch.

## What "one place" means for Buzz_002

Concrete end-state Buzz_002 will describe if asked plainly:

- **Per-association record** carrying that association's
  governing docs (current + amendment trail), meeting cycle (with
  the next AGM date *visible from the front page*), financials
  (last audit, current arrears, reserve-fund posture), vendor list
  (with active contracts and PM-schedule entries), unit-owner
  comm log (open / resolved), and compliance calendar (next test
  / inspection / refresh due).
- **Firm-wide view** sitting *above* the per-association records:
  arrears total across all associations, AGMs due in the next 60
  days, compliance items overdue, vendor invoices awaiting
  approval. The owner's morning view.
- **Per-staff role-based access** — the front-desk role sees
  intake and resolution status but not the audit reports;
  bookkeeping sees finances but not unit-owner-complaint detail.
- **Email integration that doesn't require Outlook to be the
  source of truth** — comms arrive in Outlook *and* land in the
  per-unit-owner thread automatically.
- **An export Buzz_002 owns** — the next centralisation attempt
  must not be one they can't walk away from. (The two previous
  failures both hit this.)

## Notes on role-play (for operator iteration #1)

This section is for the human operator playing Buzz_002 against
the Mode-A Essex prompt in `claude.ai/new`. It is *not* read by
Essex during the conversation.

- **Stay in character on tech comfort.** Buzz_002 understands a
  pivot table; they do not understand a JSON file. If Essex starts
  saying "schema" or "instance", Buzz_002 should respond the way
  the real owner would: politely confused, asking for plainer
  words. That's signal.
- **Surface symptoms when prompted, don't pre-diagnose.** A real
  Buzz_002 says *"I asked Joanne where the elevator contract was
  and three emails later we still didn't have it"* — they do
  **not** say *"we lack a centralised document repository with
  consistent metadata."* The latter is Essex's job to synthesise.
- **Bring up Ontario compliance only when asked.** It's real, it's
  load-bearing, but the operator-owner doesn't lead with the legal
  framing — they lead with the day-to-day annoyance.
- **Two prior failures are part of the persona.** If Essex offers
  a generic "we'll centralise everything", Buzz_002 should push
  back: *"I tried that. Twice. What's different this time?"* This
  pressure-tests Essex's framing under realistic skepticism.
- **The condo board is in the room, not just the firm.** Buzz_002
  ultimately answers to ~50 volunteer board members across the
  portfolio. If a feature could *embarrass them* at an AGM, that's
  a kill switch — surface it.

## What this file does NOT cover

- **Buzz_001 and Buzz_003** — separate archetype files when those
  iterations run. Buzz_001 will be family-friend-grounded
  (high-fidelity, low-tech-comfort); Buzz_003 (HVAC contractor) is
  deferred to production phase per §10.10.
- **Mode-A persona doc content itself** — that lives in
  [`../internal_docs/mode_a_persona_v0.md`](../internal_docs/mode_a_persona_v0.md)
  and is what Essex actually reads at conversation start. This
  archetype file is the *operator's* reference, not Essex's.
- **The bridge into Claude Code** — §8.5 of
  [`../internal_docs/entry-architecture-notes.md`](../internal_docs/entry-architecture-notes.md).
  The Buzz_002 iteration produces an anonymized summary; the
  bridge is what carries that summary into Buzz's own Claude Code
  session. Out of scope here.
