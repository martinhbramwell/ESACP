# Session 22 minutes — `/roll_out/` reckoning + `/roll_out/inside/` walkthrough; the two-model split

**Branch:** `on_boarding` (Junior). **Started from:** the standing #723 U0 build plan
(no separate agenda issue — #723 was the umbrella). **Objective met:** built and published
the reckoning road map (U1) and the full eight-stage walkthrough, then an audit surfaced a
model split that reset the go-forward plan.

## The arc
Began by executing **U1** (cost fix + reckoning page), then the operator drove a large,
many-turn build of the **`/roll_out/inside/` tabbed walkthrough** — far beyond the original
"component deep-dive" issue. Late in the session a question about stale Stage-1 copy on the
landing triggered a **multi-doc audit**, which surfaced the load-bearing finding below and
turned the remaining work into a tracked realignment.

## ESSENTIAL KNOWLEDGE — carry forward

1. **The site is split between two onboarding models** (S22 audit, memory
   [`project_canonical_greeter_model`](#)):
   - **Live front door** (`first_visit_005.md`) + **landing** (`index.md` "How it Works") use
     **transparent-Nick** — the free chat openly *is* Nick.
   - The **just-published walkthrough** (`roll_out/inside/`) uses the **U0 greeter model** —
     free chat = openly Claude; **Nick lives behind the door** in Claude Code, met after install.
2. **Decision: `roll_out/inside/` is canonical.** It's the latest pass aligning intent ×
   technical-feasibility × visitor-comfort. Prior surfaces realign to it. Correction to a
   mid-session claim: "Nick in the free chat" on the landing is *not* wrong vs. what's **live**
   (the live front door is also transparent-Nick) — it's the **walkthrough** that jumped ahead
   to the unbuilt greeter model. So the realignment is *bringing the laggards forward*, not
   fixing the new page.
3. **The realignment is coupled** — landing narrative + landing invite snippet + `first_visit_005`
   all say "Nick" and must convert together (the snippet loads the front door). That's **U2/U4 of
   #723**, tracked in **#736**; it changes live chat → needs a **live mode-2 test**. Filed, not
   started.
4. **Pre-settled for #736:** free-chat deliverable = a **"letter of introduction"** (not "summary");
   `essex-demo.md` deleted; learn-more "~60 sessions" number = don't-care.
5. **Mission & Vision is the crew's compass** — the operator added a Step-6 "Harmonizing" beat
   stating Nick helps each visitor define their M&V. That promise is backed by platform issue
   **#733** (Nick must elicit/refine/store each tenant's M&V).

## What shipped (all merged to `on_boarding` + published live to beaverdam.solutions)
- **U1 / #731** (PR #734, merge `8986dfb`) — landing cost fix (Pro *includes* Claude Code) +
  `/roll_out/` reckoning road-map page (8-step ladder, two-question self-check, off-ramp).
- **#732** (PR #735, merge `f4dec10`) — the `/roll_out/inside/` **tabbed eight-stage walkthrough**:
  7 tabs in "car you already bought" voice; the cast (dramatis personae) + M&V "Harmonizing" in
  Step 6; four-corner topology; six images; a **~75% floating iframe lightbox** for the
  commit-history video (the 1.74 GB clip is gitignored, never committed — GitHub rejects >100 MB);
  all external links open in new tabs; responsive. Absorbed the standalone `/roll_out/` page (now
  a redirect).
- **essex-demo deletion** (PR #737, merge `c0b76b0`, refs #736) — orphaned, retired "Essex" name.
- **#who panel trim** (PR #739, merge `44be381`, refs #738) — removed the public-history + background
  (learn-more) lines; orphans learn-more, tracked for an eventual revisit.

## Process notes
- **GPG pinentry** unlocked by the operator twice (`feedback_gh_signing_pinentry_timeout`) — once
  on the #732 commit ("No passphrase given"), once proactively for the essex-demo work.
- **Previews now use the operator's live `jekyll serve` at `localhost:4000`** (memory
  [`feedback_preview_operator_jekyll_serve`](#)) — I can't run `jekyll serve` (sandbox kills it).
- **QA:** #732 T1 = approve-with-conditions (typo, dead CSS, stale issue body — all cleared);
  731/732-merge T2, essex-demo T1+T2, who-panel T1+T2 all = approve (T2 advisory per
  `project_on_boarding_trunk_vs_default`). Cost facts verified live, not from memory.
- **Filed:** #733 (Nick M&V), #736 (greeter realignment, U2/U4), #738 (who-panel/learn-more revisit),
  #740 (S23 agenda), #741 (this closeout).

## State at close
| | |
|---|---|
| **Live** | reckoning + walkthrough both published on beaverdam.solutions |
| **#723** | OPEN — U0 umbrella; U1 done, U2/U4 = #736 next |
| **Next (S23)** | #736 greeter-model realignment (landing + front door, coupled) — live mode-2 test |
| **Carry-forward** | #733, #738, #721, #710, #715/#717/#719 (→U6), #694, #511, #448 |

Canonical spec: [`roll_out/inside/index.md`](../docs/roll_out/inside/index.md). Decision detail in
memory `project_canonical_greeter_model`.
