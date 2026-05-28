---
layout: default
title: "ESACP — learn more"
---

<div style="text-align: center; margin: 2.5em 0 2em;">
  <h1 style="font-size: 6em; margin: 0; line-height: 1; letter-spacing: 0.02em;">ESACP</h1>
  <p style="font-size: 1.6em; color: #555; margin: 0.4em 0 0; font-style: italic;">When your only developer leaves!!</p>
</div>

A small family-owned business in our region runs a comprehensive business management system — the kind that handles inventory, billing, payroll, taxes, customer routes, all of it. It was built up over years by a single developer who customised it deeply, to fit how this particular business actually works.

The developer is one person. They have a life. The business cannot depend on their continued availability and cannot afford to hire or train a replacement.

This is the common shape of a small business that uses powerful, customisable software: they get far enough into customisation that they cannot turn back, and then they cannot afford to keep that customisation maintained.

## What is being built

ESACP — *ERP System Administrator Control Panel* — is a maintenance environment in which a much less specialised person can hold the knowledge that used to live in the head of one developer, with AI doing the heavy lifting.

It is being built and operated right now, on a real business. Not a future product. Not a demo. In flight today, with a complete public record of every decision and every failure in the source repository.

## What it actually does

Several pieces, working together:

- **The AI is connected directly** to the running business system, in a sandboxed way. It can read the database, understand the years of customisation, propose improvements, and — after human sign-off — make them.
- **Every change the AI proposes is reviewed** by another AI before it can be committed. The system catches its own mistakes.
- **Every working session is recorded** — agenda, notes, decisions, mistakes — and each new session begins by reading those records, so coherence does not depend on any one person's memory.
- **The platform watches itself.** When something breaks at 11pm on a Friday, it tries to repair itself first and explains what it did when the maintainer wakes up.

## What is being learned

Across roughly 60 working sessions, the project has accumulated a clear picture of how AI fails at this kind of work. AI coding assistants are remarkable but they have specific, repeating failure modes — and a non-technical founder is especially exposed to most of them.

Those failure modes have been written up here:

- **[Pitfalls of Vibe-Coding a Complex Business System](pitfalls/notes.html)** — ten pitfalls in plain language, what each one looks like in practice, and what to insist on when working with an AI on your business.
- **[Slideshow version](pitfalls/slides.html)** — same content, presentation-ready.

The headline finding: **AI requires discipline, and the discipline is learnable.** It does not require the founder to learn to code. It requires them to know where to push back.

## What's next

This year crosses several milestones the small business needs:

- A safe path from the ageing version of the underlying business platform to a current one.
- Backup and restore that anyone — not just a developer — can operate.
- A visual map of the running system that a non-developer can navigate.

Beyond those: ESACP's design is generic. The current maintainer happens to know one particular business. The platform itself does not — it knows the *shape* of being a small business with a customised commercial-grade business system. That shape is reusable.

## Reading more

- **[Pitfalls — full notes](pitfalls/notes.html)** — ten things AI gets wrong, in plain language.
- **[Pitfalls — slideshow](pitfalls/slides.html)** — presentation version.
- **[Source repository on GitHub](https://github.com/martinhbramwell/ESACP)** — every commit, every issue, every decision.
