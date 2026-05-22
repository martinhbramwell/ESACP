# `on_boarding/` — starting kit

This directory is the starting kit for developing **new-operator
onboarding material** for ESACP. The kit was scoped and stocked on
the parent project's Session 68 (2026-05-20) under issue
[ESACP#406](https://github.com/martinhbramwell/ESACP/issues/406). It
is the substrate the next Claude Code session — working from a fresh
Windows 11 controller with no prior project context — will pick up
from.

The kit is small on purpose. Four files orient you; the actual
onboarding material is what you (the fresh Claude) will build from
here.

## Files in this kit

| File | What it gives you |
|---|---|
| [`ORIENTATION.md`](ORIENTATION.md) | What ESACP is, who it's for, what this branch is for, the four-stage end-user journey the onboarding material must cover, scope (in/out) |
| [`BUZZ_PERSPECTIVE.md`](BUZZ_PERSPECTIVE.md) | The Variant-1 archetype ("Buzz") in concrete form, plus the five-point onboarding contract every Stage 1–4 deliverable must satisfy. Companion to `ORIENTATION.md`; the lens layer. |
| [`POINTERS.md`](POINTERS.md) | Map into ESACP's existing repo-resident technical surface — which sections of which files are universal, which are tenant-specific |
| [`AI_GUARDRAILS.md`](AI_GUARDRAILS.md) | Conduct rules, process rules, and repo-resident guard-rail pointers — your behavioural contract on this branch |
| [`README.md`](README.md) | This file — kit index + first-session checklist |

## Working docs (under `docs/`)

These are written by Junior (the on_boarding-branch Claude) as work proceeds. The kit files above are operator-authored orientation; the files below are Junior's outputs. Read them when the kit or your operator refers you to them.

| File | What it gives you |
|---|---|
| [`docs/session-discipline.md`](docs/session-discipline.md) | Cadence rules for this branch — 1:1:N issue bundling, sub-branch flow, acceptance test for docs, QA verdict layer, parent-project precedence |
| [`docs/SESSIONS.md`](docs/SESSIONS.md) | One-line session log — one row per session, append-only. Read to see what prior sessions on this branch produced |
| [`docs/qa-log.md`](docs/qa-log.md) | Junior-side QA verdict log — notable `esacp-qa` verdicts from this branch's sessions. Brevity-protocol-curated. Companion to (not duplicate of) `internal_docs/qa-log.md` |
| [`docs/stage-2-triage.md`](docs/stage-2-triage.md) | The Stage-2 friction-list triage (Session 2): six items from #415 sorted into Bucket 1 / 2 / 3 by Buzz-relevance, plus the hybrid-shape decision (bootstrap script + wizard prompts + browser-driven signups) |
| [`docs/entry-architecture-notes.md`](docs/entry-architecture-notes.md) | Exploratory architecture (Session 3): how Buzz gets from "tapped Get Started on the Pages site" to "Essex is building a controller." Covers the corrected Junior/Buzz/Essex role model, the PWA + CF Worker + cloud-VM stack, the trust-progression sequencing (cloud rental → demonstrated value → walled garden), the Minecraft framing, the current gap inventory, and the holes still to address. **Thinking document — pre-decision.** |

## Executable kit (under `tools/`)

Scripts Buzz (or an operator on Buzz's behalf) is expected to run. Each is idempotent; safe to re-run.

| File | What it does |
|---|---|
| [`tools/bootstrap.py`](tools/bootstrap.py) | Stage-2 v0 — installs the no-credential half of the controller toolkit (`pinentry-curses`, `keychain`, `age`, `gh`, `sops`) and configures GPG cache TTL + `~/.bashrc` lines for `GPG_TTY` and `keychain`. Targets Ubuntu 22.04+ / WSL2 Ubuntu. Invoke: `./on_boarding/tools/bootstrap.py`. Closes [#431](https://github.com/martinhbramwell/ESACP/issues/431). |

## First-session checklist (zero-knowledge Claude)

Run this on first checkout of the `on_boarding` branch.

1. **Confirm you're on the right branch and it's clean.**
   ```bash
   git branch --show-current   # expect: on_boarding
   git status                  # expect: clean
   ```

2. **Read the kit in order.**
   - [`ORIENTATION.md`](ORIENTATION.md) — what you're building and for whom
   - [`BUZZ_PERSPECTIVE.md`](BUZZ_PERSPECTIVE.md) — through whose eyes every deliverable must read well
   - [`POINTERS.md`](POINTERS.md) — where the existing material lives
   - [`AI_GUARDRAILS.md`](AI_GUARDRAILS.md) — how you're expected to behave
   - [`docs/session-discipline.md`](docs/session-discipline.md) — the cadence rules (1:1:N, branch flow, acceptance test, QA layer)

3. **Read the universal sections of the root `CLAUDE.md`** —
   `POINTERS.md` flags which sections to read and which to skip as
   tenant-specific.

4. **State your objective.** One sentence. One objective per session.
   See the Session Protocol in the root `CLAUDE.md`.

5. **Ask the operator** the following before producing any onboarding
   material:
   - What's the operator's hardware posture (their controller machine,
     their target hypervisor, their cloud-VPS plan)?
   - Are they actually new to ESACP, or are they testing the
     onboarding material with prior knowledge?
   - Which of the four end-user stages do they want covered first?

6. **File a GitHub issue on `martinhbramwell/ESACP`** for the first
   piece of onboarding work before you write any of it. Bug workflow
   discipline applies to feature work too: issue first, then code,
   then `fixes #N` in the commit message.

## What's NOT in this kit and why

- **No tenant-specific material.** No tenant identifiers, no real
  hostnames, no bespoke-app references, no fleet data. The branch's
  audience is zero-knowledge; the kit reflects that.
- **No memory-dir dependencies.** The parent project keeps Claude's
  behavioural memory in a separate private repo, symlinked into
  Claude's runtime memory directory. You don't have it, end-users
  won't have it, and nothing on this branch may depend on it.
- **No turnkey onboarding material yet.** S68 (the session that
  created this kit) was scoping + scaffolding only. The actual
  onboarding material is your job from here.

## Working agreements with the operator

- **One objective per session.** If a second concern surfaces while
  you're working on the first, file it as an issue and return to the
  primary objective.
- **Conventional Commits, GPG-signed, with the co-author trailer.**
  See `CLAUDE.md` §"Commit Conventions".
- **Pull requests merge into the `on_boarding` branch.** This branch
  merges into `main` only when the operator decides the onboarding
  material has reached a deliverable state. Do not merge to `main`
  yourself.
- **The QA verdict layer applies.** Invoke the `esacp-qa` agent
  before any commit / merge / push / destructive op / issue close,
  and act on its verdict.

## Reporting back

When you finish a session's work, leave the operator a short status
note. What you produced, what's next, what's blocking. Two sentences
is usually enough. The operator does not need a transcript — they
can read the diff. They need the outcome and the next handle.

## Pointers to upstream project state

- Issue tracker: `martinhbramwell/ESACP` on GitHub
- Branch policy: see `CLAUDE.md` §"Session Protocol" (umbrella vs.
  1:1:1 vs. housekeeping bundle)
- This branch's originating issue: [ESACP#406](https://github.com/martinhbramwell/ESACP/issues/406)
- This branch's originating agenda:
  `internal_docs/SessionLogs/2026-05-20-2034-next-agenda.md`
  (read as historical context; do not adopt as your own agenda)
