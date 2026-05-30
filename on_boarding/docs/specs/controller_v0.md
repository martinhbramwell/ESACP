# Controller package spec (v0)

> **What this document is.** Reference data for the ESACP Mode-A
> advisor. When the advisor needs to assess whether one of the
> operator's computers can serve as the **controller**, it fetches
> this sheet and reads off the concrete requirements below. This is
> not operator-facing prose; it is the source the advisor reasons
> from. A competent reader — human or AI — should be able to look at
> a given computer and this sheet and decide *yes/no/with-caveats*.

---

## 1. What the controller is

The controller is the **first computer the operator touches** — the
"shoe on a string" in the shoe → string → rope → chain metaphor. Its
only job is to **bootstrap saconsole** (the management VM) and hand
off. It is *bootstrap-only*: once saconsole is live, saconsole manages
every sibling VM, and the controller's ongoing role is small.

Because it is bootstrap-only, the controller's hardware bar is **low**.
The heavy compute requirement belongs to saconsole's host (see the
saconsole spec sheet), which may be the same machine or a different
one. Do not conflate the two: a modest laptop can be a fine controller
even when it is *not* a viable saconsole host.

## 2. Operating system

| Requirement | Detail |
|---|---|
| **Supported today** | Ubuntu 22.04+ (native) or **WSL2 Ubuntu** on Windows 10/11 |
| **Architecture** | amd64 (x86-64). The `sops` install step is amd64-only in v0. |
| **Not yet supported** | macOS, native Windows, ARM Linux. Cross-OS support is tracked in [#435](https://github.com/martinhbramwell/ESACP/issues/435). |

A Windows operator does **not** need to leave Windows: WSL2 provides a
real Ubuntu inside Windows, installed in one command, with nothing
removed from the existing system. This is the recommended path for the
common "Windows + never-opened-a-terminal" operator.

## 3. The controller toolkit

The `bootstrap.py` installer puts five free tools and two small config
edits in place. It is **idempotent** (safe to re-run; each step probes
and skips if already done) and asks for the sudo password **once**.
Total download is roughly **25 MB**.

| Tool | What it does | Who provides it | Cost |
|---|---|---|---|
| **pinentry-curses** | In-terminal prompt for your GPG password | Ubuntu's own package mirrors | free, ~200 KB |
| **keychain** | Keeps SSH/GPG agents running so you type key passwords once per login | Ubuntu's own package mirrors | free, ~150 KB |
| **age** | Modern file-encryption tool — keeps passwords/keys encrypted inside the code copy | Ubuntu's own package mirrors | free, ~2 MB |
| **gh** | GitHub's command-line tool — lets ESACP manage your code copy on your behalf | GitHub (sees a download, not an identity until you sign in) | free, ~12 MB |
| **sops** | Secrets-encryption tool (CNCF) — keeps secrets encrypted at rest | GitHub (sees a download, not an identity) | free, ~10 MB |

Config edits the installer makes:
- **GPG password cache (8 h)** in `~/.gnupg/gpg-agent.conf` — so you do
  not re-type your GPG password every commit.
- **Shell environment** (`GPG_TTY` + `keychain`) appended to `~/.bashrc`
  — so GPG knows which terminal to prompt on and passwords cache across
  shells.

> Source of truth for this table is `on_boarding/tools/bootstrap.py`
> (the `Prose` entries). If the two ever disagree, `bootstrap.py` wins
> — see [#518](https://github.com/martinhbramwell/ESACP/issues/518) for
> the planned generate-from-source step that will remove the drift.

## 4. Claude Code (the AI driver)

The controller also needs **Claude Code** — the AI that actually drives
the install and the later ERP-maintenance work. For the Mode-A
discovery conversation, a free claude.ai account is enough (this is how
the operator reached this advisor). Running Claude Code on the
controller itself requires an Anthropic account; the free tier is
sufficient to begin. No credential is ever entered on the operator's
behalf — the operator types every password and clicks every final
"I agree" themselves.

## 5. Convergence checklist (what the advisor decides)

Given a candidate computer, the controller is viable when **all** hold:

1. Runs Ubuntu 22.04+ **or** can run WSL2 Ubuntu (Windows 10/11), on amd64.
2. Has internet access (to download the toolkit and reach GitHub/Anthropic).
3. The operator can obtain sudo on it (install rights).
4. Has a free claude.ai / Anthropic account, or is willing to create one.

If a candidate fails only on OS (e.g. macOS / ARM), record it as
**blocked-on-#435**, not a hard no. If it passes all four, it is a
controller — independent of whether it can also host saconsole.
