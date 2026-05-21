# Stage-2 friction triage — by Buzz-relevance

> **Status:** decision doc, Session 2 of the `on_boarding` branch. ·
> **Closes the agenda of:** [#419](https://github.com/martinhbramwell/ESACP/issues/419). ·
> **Triages:** [#415](https://github.com/martinhbramwell/ESACP/issues/415). ·
> **Lens:** [`BUZZ_PERSPECTIVE.md`](../BUZZ_PERSPECTIVE.md).

## Why this doc exists

The Stage-2 friction backlog in [#415](https://github.com/martinhbramwell/ESACP/issues/415)
was discovered *by Junior on a fresh WSL2 controller*, not by Buzz (the
Variant-1 archetype in [`BUZZ_PERSPECTIVE.md`](../BUZZ_PERSPECTIVE.md)).
Junior-calibrated friction is not Buzz-calibrated friction. Before any
of the six items becomes a deliverable, the list must be re-read through
Buzz's eyes — which items he genuinely hits, which are
Claude-tooling-only pathologies, and which are universal-convenience
defaults the controller setup should just *do* without Buzz ever
reading about them.

[#419](https://github.com/martinhbramwell/ESACP/issues/419) pre-triaged
the six items into three buckets and asked Session 2 to ratify or
refine. This doc does that work and adds the deliverable-shape decision
[#419](https://github.com/martinhbramwell/ESACP/issues/419)'s
acceptance criteria require.

## The three buckets

| Bucket | Meaning | Stage-2 role |
|---|---|---|
| **1 — Claude-tooling-only** | Pathologies of non-TTY bash subshells or of CLI-driven workflows Buzz never invokes. | Configured silently by the controller bootstrap on Buzz's behalf because *Claude* on Buzz's controller will trip on them. Buzz never sees them; they have no operator-facing material. |
| **2 — Universal convenience** | Annoyances that affect everyone (Buzz on rare manual moments, AI on every transaction) but require no operator decision. | Configured silently by the controller bootstrap as a sensible default. No operator-facing material. |
| **3 — Buzz genuinely hits** | Real, universally-needed steps Buzz cannot avoid touching: account creation, credential typing, identity declaration. | First-class Stage-2 deliverable surface. Each one must pass the five-point contract in [`BUZZ_PERSPECTIVE.md`](../BUZZ_PERSPECTIVE.md) §"Buzz's onboarding contract". |

The buckets are not a sorting hat — they are a *delivery-mode* taxonomy.
Bucket 1 and Bucket 2 items are still *real work* that must happen; the
distinction is who experiences them. Buzz only sees Bucket 3.

## Triage of #415's six items

| #415 item | Bucket | One-line reason |
|---|---|---|
| 1. `gh` not preinstalled | **3** | Buzz's GitHub fork is the load-bearing piece of his "won't lose my system" story (BUZZ_PERSPECTIVE §"Service-by-service framings"). `gh` is the tool by which ESACP drives that fork on his behalf. He doesn't run `apt`, but the install happens because *he* authorised it. |
| 2. Git identity not configured | **3** | Every change to Buzz's business system is signed with his name. He must declare that identity; it is not Claude's identity, and Buzz isn't a tenant abstraction. |
| 3. Non-TTY GPG pinentry failure | **1** | Buzz commits through Cytoscape, not from a non-TTY subshell. The pathology is Claude-Code's bash-subshell environment on Buzz's controller. Configure silently. |
| 4. GPG cache TTL = 10 min | **2** | Reprompt-every-10-min annoys both Buzz (on rare manual commits) and Claude (on every transaction). Reprompts in non-TTY shells also fail per item 3 ─ a 10-minute TTL is a double-loss. Set 8h default; no decision surface. |
| 5a. SSH-key gen + GitHub registration | **3** | Buzz needs an SSH key registered with his GitHub account. Both halves (key generation, key registration on github.com) involve credential moments only Buzz can authorise. |
| 5b. Non-TTY `ssh-agent` / `keychain` | **1** | Front-loading `ssh-agent` + `gpg-agent` via `keychain` so child shells inherit the env vars is purely Claude-Code's problem. Buzz never sees a child shell. Configure silently. |
| 6. `gh pr edit` Projects-classic bug | **1** | Buzz never calls `gh pr edit`. Claude does. The REST workaround lives in operator-side Claude memory (already captured: `feedback_gh_pr_edit_workaround.md`); the long-term resolution is an upstream `gh` upgrade. No operator-facing material. |

### Verdict

The agenda's pre-triage in [#419](https://github.com/martinhbramwell/ESACP/issues/419)
holds without refinement. Item 5's split into 5a (Bucket 3) and 5b
(Bucket 1) is the only clarification; #419 already noted this in
parentheses ("in its non-TTY aspect").

### Lens commentary — why these buckets, not others

Two ways the triage could go wrong are worth naming so future
sessions don't re-litigate:

- **"Buzz should know what's happening on his machine, so put everything in Bucket 3."**
  Rejected. BUZZ_PERSPECTIVE §"Buzz's onboarding contract" §1 ("Buzz is
  in control") and §2 ("Visibly safe") are not "Buzz reads every
  paragraph of every config change". They are "no action happens without
  his go-ahead" and "every action has a What/Why/Who/Cost in business
  language". A `keychain` config line in `~/.bashrc` has neither a Who
  nor a Cost in Buzz's framing — it is internal plumbing. Putting it in
  Bucket 3 would be performative transparency that exhausts Buzz's
  attention budget on items that have no business meaning.
- **"Claude can run on Buzz's controller without these fixes if it's careful."**
  Rejected. The fixes are cheap and the pathologies are silent
  (especially item 3 — `Inappropriate ioctl for device` is not a normal
  user-visible error). A controller that *might* work or *might* corrupt
  a session depending on whether GPG happens to be cached fails
  BUZZ_PERSPECTIVE §"Confidently within ESACP's range". The bootstrap
  must configure Bucket 1 + Bucket 2 unconditionally.

## Stage-2 deliverable shape

[#419](https://github.com/martinhbramwell/ESACP/issues/419) asked Session
2 to decide the *shape* of Stage 2's material: long-form docs vs.
bootstrap script vs. per-OS installer vs. browser-driven steps vs. GUI
wizard. The buckets above force a shape that is none of the candidates
alone.

### The shape: hybrid, three modes

| Mode | Used for | Buzz's experience |
|---|---|---|
| **Bootstrap script (controller-side)** | Bucket 1 + Bucket 2: `pinentry-curses` install, `gpg-agent.conf` cache TTL, `keychain` install + `.bashrc` line, GPG-TTY export. Bucket 3 *prerequisites* with no credential surface: `gh` install, `sops` install, `age` install. | "Shall I install the toolkit your controller needs? It's about 40 MB and takes a minute." → "yes" → progress bar → "done." |
| **Wizard prompts (controller-side)** | Bucket 3 with declaration surface but no third-party credential: git identity (`user.name`, `user.email`), GPG-key generation (name + email passphrase), `git config user.signingkey` + `commit.gpgsign true`. | "What name should sign changes to your business system?" → "What email?" → "Choose a passphrase for your signing key (you'll re-enter it once per work session)." → key generated. No `gpg --gen-key` from memory; no `git config --global` to retype. |
| **Browser-driven (operator-side, ESACP-assisted)** | Bucket 3 with third-party credential: GitHub signup (or login), SSH-key paste into github.com settings, GitHub OAuth approvals, future CloudFlare / cheap-VM signups. | "I'm opening the GitHub signup page. I've prefilled your username and email — type your password and click 'Sign up'." → page opens → Buzz types password → "now I'll show you where to paste this SSH key." This matches [`BUZZ_PERSPECTIVE.md`](../BUZZ_PERSPECTIVE.md) §"The signup-services nuance" verbatim. |

### Why hybrid, not any single mode

- **Pure long-form docs fail Anchoring** (BUZZ_PERSPECTIVE §3): a
  12-step `apt install` walkthrough reads like dev advice. Buzz closes
  the tab.
- **Pure bootstrap script fails Visibility** (§2) for signup steps:
  Anthropic-platform rules forbid Claude from typing the GitHub
  password, and a `curl … | bash` that silently exits at the first
  credential moment leaves Buzz stuck.
- **Pure GUI wizard fails Confidence** (§4): a half-finished wizard that
  only handles identity declaration but punts the SSH-key paste to a
  manual instruction is the worst of both. Splitting modes by the
  *nature of each step* (silent, declaration, credential) is the only
  combination that passes all five contract points.

### What the shape says about PR cadence

Once Stage 2's deliverables are *script + wizard + browser-driven flow*
rather than markdown pages, PRs shift from `docs(on_boarding):` to
`feat(on_boarding):` with real Python (or shell) code and tests. Per
`session-discipline.md` §"Branch-specific additions", this is fine —
the 1:1:N cadence still works, per-PR weight goes up modestly, the
N-cap of 5–10 is intact.

A consequence worth flagging: **the bootstrap script must itself be
runnable on the three controller OSs the kit promises to cover
(Windows + WSL2, macOS, Linux).** The "every documented command was
run on the target OS before publish" rule from `session-discipline.md`
applies equally to scripts: cross-OS testing matrix is real work and
will pace Stage-2 delivery. First PRs target the Junior's actual
controller (Ubuntu WSL2); other OSs land later with an
"untested on `<OS>`, contributions welcome" notice per the cadence rule.

## Follow-up issues to file (sketched, not filed here)

These are *seeds*, not the deliverables themselves. Filing them is a
later session's job — likely the next session, with each issue
becoming its own sub-branch under 1:1:N discipline. Per
`session-discipline.md` §"Inline-fix-then-bundle", filing nine
forward-looking issues mid-doc is theatre; capture them here so the
next Junior can do it from one place.

1. **Stage-2 bootstrap script v0 — controller toolkit install.**
   Bucket 1 + Bucket 2 + Bucket-3-prerequisites (no credential surface).
   Target: Ubuntu WSL2. Covers `pinentry-curses`, `gpg-agent.conf` TTL,
   `keychain` + `.bashrc`, `GPG_TTY` export, `gh`/`sops`/`age` install.
   Acceptance: idempotent re-runs; fresh-WSL2 verification before
   publish. Closes #415 items 3, 4, 5b, and prerequisites of 1.
2. **Stage-2 wizard prompts v0 — identity + GPG key.**
   Bucket 3 declaration surface. Prompts for git identity and GPG-key
   passphrase; runs `gpg --batch --gen-key` from a generated
   parameter file (no `gpg --gen-key` from memory). Sets
   `user.signingkey` + `commit.gpgsign true`. Closes #415 item 2.
3. **Stage-2 browser-driven flow v0 — GitHub signup + SSH-key paste.**
   Bucket 3 credential surface. Uses Claude-in-Chrome (or operator's
   own browser with copy-paste guidance) to walk through GitHub
   signup/login, generate the SSH key locally, paste the public half
   into github.com settings. Hard guard: never autotypes credentials.
   Closes #415 item 5a.
4. **`gh pr edit` upstream-fix watch.**
   Track upstream `gh` releases for the Projects-classic mutation fix.
   When a fixed version ships, retire the REST workaround in operator
   memory. Closes #415 item 6 (deferred until upstream resolves).
5. **Cross-OS controller-bootstrap matrix.**
   Once items 1–3 are green on Ubuntu WSL2, extend to macOS and
   Windows-native. Each OS gets its own sub-branch and acceptance
   verification on a real fresh box. This is the work that takes Stage
   2 from "Junior's controller works" to "the four kit OSs are
   covered" — likely multi-session, candidate for `umbrella/stage-2`
   per the parent project's umbrella rules.

Items 1–3 are co-requisite for *any* Stage-2 deliverable to be
end-to-end usable by Buzz. Item 4 is independent and may sit open.
Item 5 follows once 1–3 are validated on the reference OS.

## What this doc does NOT decide

- **Which scripting language for the bootstrap.** Shell vs. Python vs.
  per-OS native is open. Likely shell for the install-only path
  (`apt`/`brew`/`winget` portability is shallow) and Python for the
  wizard. Decide in the first script-PR's plan-in-chat.
- **Cytoscape's role in Stage 2.** Per [`ORIENTATION.md`](../ORIENTATION.md)
  §"The end-user journey", Cytoscape arrives in Stage 3. Stage 2's
  deliverables stop at "controller is ready to drive the hypervisor" —
  no Cytoscape UI yet.
- **Variant-2 (maintainer-dependent customisation).** Out of scope per
  [`BUZZ_PERSPECTIVE.md`](../BUZZ_PERSPECTIVE.md) §"What this file does
  NOT cover". The shape decided here serves Variant 1 only.

## Precedence

If this doc conflicts with [`BUZZ_PERSPECTIVE.md`](../BUZZ_PERSPECTIVE.md),
the lens wins and this doc is the bug. If it conflicts with the kit's
top-level docs ([`README.md`](../README.md),
[`ORIENTATION.md`](../ORIENTATION.md), [`POINTERS.md`](../POINTERS.md),
[`AI_GUARDRAILS.md`](../AI_GUARDRAILS.md)) or with `session-discipline.md`,
those win.

If it conflicts with Anthropic-platform safety rules — specifically the
constraint that Claude cannot create accounts, type passwords, or
authorise financial transactions on a user's behalf — the safety rules
win unconditionally, and the hybrid-shape rows above that depend on
that constraint (browser-driven, operator types the password) are the
canonical reading.
