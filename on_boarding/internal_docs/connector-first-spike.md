# Connector-first architecture spike (#621)

**Status:** complete — Session 17, 2026-06-06.
**Type:** spike (time-boxed investigation; produces a decision, not code).
**Question put by the operator (S16):** does a Beaverdam-hosted **remote-MCP
custom connector** let a **free-plan** Claude.ai visitor do real
onboarding/install work *before or without* paying for Claude Code — and if so,
what does that do to the persona doc's "Claude Code is the one unavoidable cost"
claim?

Feeds [`entry-architecture-notes.md`](entry-architecture-notes.md) (#448, Paths
B/C). Unblocks the [`first_dialog.md`](../docs/first_dialog.md) scarcity rewrite
(#622).

---

## TL;DR (the decision)

**A free-plan remote-MCP connector does NOT overturn "Claude Code is the one
unavoidable cost" for Beaverdam's core use case — but it is not nothing.**

The single fact that decides it: a custom connector is reached **from
Anthropic's cloud, not from the visitor's device**
([support.claude.com 11176164](https://support.claude.com/en/articles/11176164):
*"Custom connectors connect to your MCP server from Anthropic's cloud, not from
your local device."*). Beaverdam's proposition is a self-maintaining ERP
(ERPNext managed by **saconsole**) running on infrastructure the owner controls.
The **controller is not that infrastructure** — it is a throwaway bootstrap
sandbox whose only job is to **find a home for saconsole** and hand off; after
handoff saconsole manages all the sibling VMs and the controller can be
discarded. But the bootstrap still has to run **on a real machine** the operator
controls, and nothing reached from Anthropic's cloud can touch that machine. So
the bootstrap step still needs something running locally — Claude Code (or, later,
an installed agent) — to drive the sandbox that lands saconsole on its host. The
connector lives on the wrong side of the network boundary to do that bootstrap.

What the connector **can** do is make the free-tier conversation *do real
work that isn't local-machine work* — persist the visitor's brain-dump
server-side so it survives into their eventual Claude Code, register them, fetch
live spec/recipe data, file/read their GitHub issues via a server-side token.
That is a genuine capability gain for Mode-A, just not a replacement for the paid
step.

**Recommendation:** keep the "Claude Code is the one unavoidable cost" claim
(it is still true whenever saconsole's host is operator-owned hardware), and treat the connector as an
**optional Mode-A enhancement layer**, not a precondition and not a cost
substitute. Pursue it on the entry-architecture track (#448), not as a blocker
on the doc. The #622 scarcity rewrite can therefore proceed now.

---

## Q1 — What can the free-plan connector path actually do, vs. what genuinely needs Claude Code?

The network boundary is everything. Two columns:

### A connector (cloud-reached) CAN do
- **Read/write a Beaverdam-hosted public API.** Capability is declared per
  tool; free plan supports read *and* write (org controls can restrict to
  read-only — [11176164](https://support.claude.com/en/articles/11176164)).
- **Persist conversation state server-side.** The biggest near-term win:
  capture the visitor's brain-dump / qualifying answers into a Beaverdam record
  so their *first* Claude Code session starts already knowing them. This is
  exactly the hand-off §7.3 of the persona doc promises ("your very first
  conversation with it already knows everything you just told me") — today that
  hand-off is aspirational; a connector makes it real.
- **Server-side lookups:** live spec sheets, install recipes, FAQ/pitfalls
  content, "is this hardware enough" reference data — without burning the
  visitor's turn-budget on fetches.
- **GitHub on the visitor's behalf via a server-side token** (file an issue,
  read project history) — the connector holds the credential, not the visitor.
- **Drive cloud-side infrastructure** — e.g. a Beaverdam-operated VPS. This is
  the one path where a connector *could* approach "real bootstrap work": if
  saconsole's host (and the bootstrap sandbox) live on **cloud VMs**
  (entry-architecture Path C), a cloud-reached connector can reach them. See
  Q-cloud below.

### Only Claude Code (runs ON the visitor's machine) CAN do
- **Touch the visitor's local computer at all** — examine actual hardware,
  read their filesystem, see what's installed. The persona doc's §4 feasibility
  check is reduced to *asking* precisely because Mode-A can't look; a connector
  doesn't change that, because it's still cloud-side.
- **Run the bootstrap** — drive the throwaway controller sandbox that finds
  saconsole a home and hands off. This is the irreducible local step: it
  provisions onto a machine the operator controls, which the cloud connector
  cannot reach.
- **Long-running, multi-step operations** — a Claude.ai chat is turn-based and
  budget-bounded; the bootstrap pipeline is neither. Claude Code is built for the
  long-running shape.
- **The second-AI review loop on local changes** — review of changes landing on
  operator-controlled infrastructure is a Claude-Code-side pipeline concern. (A
  connector *could* host a cloud-side reviewer for cloud-side work, but not for
  changes on a local machine.)

**Conclusion:** the dividing line is not free-vs-paid, it is
**cloud-reachable vs. on-a-machine-the-operator-controls**. Claude Code's
irreducible value is that it runs *on that machine* to perform the bootstrap;
once saconsole is handed off the controller is discarded, but getting saconsole
there is the step the connector can't do. The connector adds a cloud capability
layer to the free conversation; it does not cross the boundary to the operator's
own hardware.

---

## Q-cloud — the one path that bends the rule: cloud controller

If the **bootstrap sandbox and saconsole's eventual host are both cloud VMs**
(entry-architecture Path C, "cloud-VM-as-controller") rather than the operator's
own hardware, then a cloud-reached connector and that infrastructure are on the
*same* side of the boundary, and the connector *could* drive the bootstrap and
ongoing maintenance for a free-plan visitor.

This does not contradict the TL;DR — it relocates the question. It means the
"is Claude Code unavoidable?" answer is **topology-dependent** — specifically on
where saconsole's host lives, not on the throwaway controller, which is discarded
either way:
- **Operator-owned hardware (the documented default):** the bootstrap must run
  locally → Claude Code unavoidable. ✅
- **Fully cloud-hosted (not yet built):** a connector path is *conceivable*
  without Claude Code — but inherits the cost, trust, and data-sovereignty
  trade-offs that the local-first design exists to avoid (the Minecraft
  "your own computer" north star). Out of scope for this spike; logged for #448.

---

## Q2 — by-URL vs. directory-listing for the cold-visitor flow

| | **By URL** | **Directory listing** |
|---|---|---|
| Visitor action | Paste URL into Settings → Connectors → Add custom connector | One click in *Browse plugins* |
| Anthropic gate | None | Manual vetted review |
| Trust signal to visitor | ⚠️ shows **"unverified service"** warning | ✅ looks first-party / trusted |
| Available | **Today** | After review (weeks; gated) |
| Prerequisites | A reachable HTTPS MCP server | Production hosting + **public privacy policy** (missing = instant reject) + OAuth + reviewer test account + `readOnlyHint`/`destructiveHint` annotations |

**The collision:** the cold visitor is **Buzz** — low tech-comfort, trust is the
whole game (BUZZ_PERSPECTIVE.md's "visibly safe"). The only near-term option
(by-URL) throws an **"unverified service" security warning** at exactly the
person least equipped to evaluate it — directly undercutting the persona's
trust-building job. The option that *reads* as safe (directory listing) is the
one we can't ship yet and that Anthropic gatekeeps.

**Conclusion:** by-URL is the only buildable path now but is a poor fit for a
cold, non-technical visitor's first contact. If the connector is pursued, the
right sequencing is: prove value behind by-URL with *warm* / already-converted
operators first, and treat **directory listing as the prerequisite for ever
putting a connector in the cold Mode-A flow** (its privacy-policy + annotation
requirements are also just good hygiene). Do not put an "unverified service"
warning in front of Buzz.

---

## Q3 — Impact on the persona doc's claims

The doc was already partly self-correcting:

1. **"Must set up that one custom connector in Settings"** — **already gone.**
   The #616 v2 rewrite removed all connector-setup instructions from
   `first_dialog.md`. There is nothing in the live doc to retract. (The claim
   survives only in the S16 memory note; this spike supersedes it.)

2. **"Claude Code (~USD 20/mo) is the one unavoidable cost"** — **keep it.** It
   is true for the documented operator-owned-hardware path, and Q1 shows the connector
   does not substitute for it. No edit required on cost grounds.

3. **The scarcity / credit-run-out framing** (#622) — **independent of this
   spike; clear to fix now.** The spike's only bearing on #622 was the risk that
   connector findings would rewrite the cost/connector claims #622 touches. They
   don't (claim 1 already gone, claim 2 stands). So #622 is **unblocked** and can
   proceed to remove the false-premise scarcity pressure on its own merits
   (free plan resets ~5h rolling, not run-out — `feedback_verify_usage_mechanics`).

**Net doc impact:** no cost/connector edits required. #622 proceeds as a
standalone scarcity-framing rewrite.

---

## Follow-ups (for the operator / future sessions)

- **#622** — unblocked; scarcity-framing rewrite of `first_dialog.md` can run as
  its own 1:1:1 session.
- **#448 (entry-architecture)** — log two items: (a) "persist brain-dump
  server-side via connector so the Claude Code hand-off is real" as the
  highest-value connector use even on the operator-owned-hardware path;
  (b) full cloud-hosting (Path C) is the only topology where a connector could
  replace Claude Code — re-open the cost question only there.
- **#602 / #601 (discovery rework)** — not reframed by this outcome; the paid
  Claude-Code-side install planner stays the home for bootstrap planning, since
  only something on the operator's machine can see it.
- **Memory** — update `project_claudeai_free_connector_capability` to point at
  this spike's conclusion (connector = enhancement layer, not cost substitute;
  boundary is cloud-vs-local, not free-vs-paid).

## Sources

- [support.claude.com 11176164 — Use connectors to extend Claude's capabilities](https://support.claude.com/en/articles/11176164) (cloud-reached, not local device; free = 1 connector; read/write org controls)
- [support.claude.com 11175166 — Get started with custom connectors using remote MCP](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
- [support.claude.com 11503834 — Build custom connectors via remote MCP servers](https://support.claude.com/en/articles/11503834-build-custom-connectors-via-remote-mcp-servers)
- S16 memory `project_claudeai_free_connector_capability` (directory-listing submission requirements; UI inspection of free Buzz/test003 account)
