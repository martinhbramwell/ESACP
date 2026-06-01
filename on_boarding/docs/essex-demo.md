---
layout: default
title: "Setting up Beaverdam on a Windows 11 machine"
subtitle: "A first conversation between Buzz_000 and Nick, your Beaverdam Specialist Expert. Static mock — no chatbot wired up yet."
---

<!--
  Static chat-bubble mock. Each turn is a div with class "turn buzz" or
  "turn essex". The inner div uses `markdown="1"` so kramdown still
  processes the bubble content. No JS, no chatbot.

  Walkthrough beats (see #467 acceptance):
    1. Why a parallel Ubuntu-24.04 WSL distro
    2. The one PowerShell line that imports it
    3. Visual branding so Buzz can tell ESACP's window apart
    4. Snapshot / revert posture (Minecraft "shelter")
    5. The first prompt in the new shell + what Nick does next
-->

> **Audience:** Variant 1 greenfield (small business not yet on any ERP) ·
> **Archetype:** Win-11 controller, never opened a terminal, mobile-first ·
> **Stage:** 1 — first encounter.

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
Hi. A friend told me Beaverdam could help me get my business onto one piece of software instead of the seven I'm using now. I've got a Windows 11 laptop. Where do I start?
  </div>
</div>

<div class="turn essex">
  <div class="speaker">Nick</div>
  <div class="bubble" markdown="1">
Welcome, Buzz. The first thing we'll do is give your laptop a small, separate Linux room to work in — without touching anything you already have on Windows. The piece of Windows that lets us do this is called **WSL** (Windows Subsystem for Linux); it's free, it's made by Microsoft, and it ships with your laptop already.

Think of it like adding a clean workbench to your garage. Your existing tools stay where they are; we just put the Beaverdam work on its own surface so nothing gets mixed up.

When you're ready, I'll walk you through the first command.
  </div>
</div>

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
Hold on — I already had someone install Ubuntu on this thing last year for a different project. Won't yours wreck that one?
  </div>
</div>

<div class="turn essex">
  <div class="speaker">Nick</div>
  <div class="bubble" markdown="1">
Good catch, and the answer is *no, by design*. WSL lets you run several Linux installations side by side, each with its own name and its own files. We're going to create a brand-new one called **ESACP** and leave your existing Ubuntu completely alone.

Here's the plan, and I'll narrate every step before we run it:

- **What** — install a fresh Ubuntu 24.04, then re-import it under the name `ESACP`.
- **Why** — a separate name means a separate filesystem. If anything ever goes wrong with the ESACP side, your other Ubuntu is untouched.
- **Who** — only Microsoft (the WSL feature) and Canonical (the people who make Ubuntu). Nobody else is involved at this step.
- **Cost** — zero. The disk space comes out of your laptop's drive (around 1.5 GB to start).

Open **PowerShell** — the blue terminal, not the black one — and we'll do it together.
  </div>
</div>

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
Got it open. Now what?
  </div>
</div>

<div class="turn essex">
  <div class="speaker">Nick</div>
  <div class="bubble" markdown="1">
Two commands. The first one downloads Ubuntu 24.04 from Microsoft's catalogue:

```powershell
wsl --install -d Ubuntu-24.04 --no-launch
```

The `--no-launch` is intentional — we don't want it to start asking *you* for a username yet. It'll just sit there, ready.

When that finishes (a minute or two), tell me and we'll do the second one.
  </div>
</div>

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
Done. It said "Ubuntu-24.04 has been installed."
  </div>
</div>

<div class="turn essex">
  <div class="speaker">Nick</div>
  <div class="bubble" markdown="1">
Perfect. Now we'll make the ESACP-branded copy. Three lines:

```powershell
mkdir C:\WSL\ESACP
wsl --export Ubuntu-24.04 C:\WSL\ESACP\seed.tar
wsl --import ESACP C:\WSL\ESACP C:\WSL\ESACP\seed.tar --version 2
```

In plain English: we made a folder, took a snapshot of the fresh Ubuntu you just installed, and registered that snapshot back under the name **ESACP**. You now have a Linux distribution called `ESACP` that is yours.

Type `wsl -l -v` and you should see both `Ubuntu-24.04` and `ESACP` in the list.
  </div>
</div>

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
There they are. So now I just open the ESACP one?
  </div>
</div>

<div class="turn essex">
  <div class="speaker">Nick</div>
  <div class="bubble" markdown="1">
Almost. One more thing first — let's make the ESACP window *look* different from the other one, so you never have to guess which is which. This is a one-time setup in **Windows Terminal** (the app with the multicoloured icon in your Start menu).

Open Windows Terminal, click the **down-arrow** next to the `+` tab, choose **Settings**, then **Open JSON file**. We'll add a profile for ESACP. I'll give you the exact block to paste:

```json
{
  "name": "ESACP",
  "commandline": "wsl.exe -d ESACP",
  "icon": "🛠️",
  "tabTitle": "ESACP",
  "colorScheme": "Tango Dark",
  "background": "#0f2a1d",
  "startingDirectory": "//wsl$/ESACP/root"
}
```

Save the file. Open a new tab — you'll see **ESACP** in the dropdown, in a deep-green window that's unmistakable.

- **What** — a named, coloured terminal profile for ESACP.
- **Why** — when you have three windows open and you're tired, the green one is always ESACP. Mistakes get cheaper.
- **Who** — nobody outside Microsoft. The setting lives in a file on your laptop.
- **Cost** — free.
  </div>
</div>

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
That's cute. Green window, ESACP. Got it. What if I mess everything up?
  </div>
</div>

<div class="turn essex">
  <div class="speaker">Nick</div>
  <div class="bubble" markdown="1">
That's the best question you've asked yet, and we have a clean answer.

Before we change anything inside the ESACP room, we'll take a **snapshot** — a complete copy of the room as it is right now. If anything goes sideways later, you run one command and you're back to this exact state. Nothing else on your laptop is affected.

Snapshot (run from PowerShell, not from inside ESACP):

```powershell
wsl --export ESACP C:\WSL\ESACP\snapshots\day-0.tar
```

Revert, if you ever need to:

```powershell
wsl --unregister ESACP
wsl --import ESACP C:\WSL\ESACP C:\WSL\ESACP\snapshots\day-0.tar --version 2
```

I think of it as the **shelter** in a Minecraft survival world — a safe place you can always return to. An IT consultant would charge you several hundred dollars to set up a backup-and-restore system this clean. We just did it in two lines, and you own it.
  </div>
</div>

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
OK. Snapshot taken. Now do I go in?
  </div>
</div>

<div class="turn essex">
  <div class="speaker">Nick</div>
  <div class="bubble" markdown="1">
Now you go in. Open the green **ESACP** tab in Windows Terminal. You'll see a prompt that looks something like this:

```text
root@ESACP:~#
```

You're inside the ESACP room. From here I'll start the actual setup — installing the small set of tools the platform needs (a key manager, a signing utility, GitHub's command-line client, and a couple of others). Every install will get the same *What / Why / Who / Cost* explanation you've seen so far, and you'll click "yes" to each one.

An IT consultant would take weeks to wire up everything we're about to set up, and would charge you accordingly. Beaverdam has all of it in its training. We'll go through it together at your pace.

When you're ready, type `whoami` and press Enter. We'll start there.
  </div>
</div>

<div class="turn buzz">
  <div class="speaker">Buzz</div>
  <div class="bubble" markdown="1">
*[end of static mock — the next turns will come from the real chatbot when the backend lands. See `on_boarding/internal_docs/entry-architecture-notes.md`.]*
  </div>
</div>
