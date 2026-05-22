#!/usr/bin/env python3
"""ESACP on_boarding — controller toolkit installer (v0).

Stage-2 bootstrap: installs the no-credential half of the controller
toolkit (pinentry-curses, keychain, age, gh, sops) and configures GPG
cache TTL + bashrc lines for GPG_TTY and keychain.

Targets Ubuntu 22.04+ / WSL2 Ubuntu. Cross-OS support is tracked in
https://github.com/martinhbramwell/ESACP/issues/435.

Idempotent: safe to re-run. Each step probes its target state and
skips if already configured.

Closes https://github.com/martinhbramwell/ESACP/issues/431.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


# ── Data ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Prose:
    name: str
    what: str
    why: str
    who: str
    cost: str


SOPS_DEB_URL = (
    "https://github.com/getsops/sops/releases/download/v3.9.4/"
    "sops_3.9.4_amd64.deb"
)


# ── Prose (Buzz contract: visibility + confident tone) ────────────


def announce(p: Prose) -> None:
    print(f"\n→ Installing {p.name}")
    print(f"  What:  {p.what}")
    print(f"  Why:   {p.why}")
    print(f"  Who:   {p.who}")
    print(f"  Cost:  {p.cost}")


def announce_skip(p: Prose) -> None:
    print(f"  ✓ {p.name} — already installed, skipping")


def announce_config(name: str, what: str, why: str, effect: str) -> None:
    print(f"\n→ Configuring {name}")
    print(f"  What:  {what}")
    print(f"  Why:   {why}")
    print(f"  When:  {effect}")


# ── Control (Buzz contract: confirm before acting, pause on failure) ──


def confirm_proceed() -> None:
    print()
    print("This script will install a small set of free tools and add a few")
    print("lines to two config files in your home directory. It will ask for")
    print("your sudo password once for the system installs. Previously-done")
    print("steps are detected and skipped, so re-running is safe.")
    print()
    ans = input("Shall we proceed? [y/N] ").strip().lower()
    if ans not in ("y", "yes"):
        print("OK — no changes made. Exiting.")
        sys.exit(0)


def failure_prompt(step: str, detail: str) -> str:
    print()
    print(f"⚠  Step '{step}' failed: {detail}")
    print()
    while True:
        ans = input("Choice [r=retry / s=skip / a=abort]: ").strip().lower()
        if ans in ("r", "s"):
            return ans
        if ans == "a":
            print("Aborting. Already-completed steps remain in place.")
            sys.exit(1)
        print("Please type r, s, or a.")


# ── Probes ────────────────────────────────────────────────────────


def has_binary(name: str) -> bool:
    return shutil.which(name) is not None


def has_dpkg_pkg(pkg: str) -> bool:
    result = subprocess.run(
        ["dpkg", "-s", pkg],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


# ── Installs ──────────────────────────────────────────────────────


def sh(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False)


def install_apt(pkg: str) -> bool:
    """apt update + apt install. Returns True on success."""
    upd = sh(["sudo", "apt-get", "update", "-qq"])
    if upd.returncode != 0:
        return False
    ins = sh(["sudo", "apt-get", "install", "-y", pkg])
    return ins.returncode == 0


def install_gh_repo() -> bool:
    """Add GitHub CLI apt repo, then apt install gh."""
    keyring_url = "https://cli.github.com/packages/githubcli-archive-keyring.gpg"
    keyring_path = "/etc/apt/keyrings/githubcli-archive-keyring.gpg"
    list_path = "/etc/apt/sources.list.d/github-cli.list"
    arch = subprocess.run(
        ["dpkg", "--print-architecture"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    list_line = (
        f"deb [arch={arch} signed-by={keyring_path}] "
        "https://cli.github.com/packages stable main\n"
    )
    steps: list[list[str]] = [
        ["sudo", "mkdir", "-p", "-m", "755", "/etc/apt/keyrings"],
        ["sudo", "curl", "-fsSL", "-o", keyring_path, keyring_url],
        ["sudo", "chmod", "go+r", keyring_path],
        ["sudo", "tee", list_path],
    ]
    for i, step in enumerate(steps):
        stdin_data = list_line.encode() if step[-1] == list_path else None
        result = subprocess.run(
            step,
            input=stdin_data,
            capture_output=(stdin_data is not None),
            check=False,
        )
        if result.returncode != 0:
            return False
    return install_apt("gh")


def install_sops_deb() -> bool:
    """Download sops .deb and dpkg install it. v3.9.4, amd64 only."""
    if subprocess.run(
        ["dpkg", "--print-architecture"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip() != "amd64":
        print("  sops .deb install supports amd64 only; skipping on this arch")
        return False
    with NamedTemporaryFile(suffix=".deb", delete=False) as tmp:
        deb_path = tmp.name
    try:
        urllib.request.urlretrieve(SOPS_DEB_URL, deb_path)
        result = sh(["sudo", "dpkg", "-i", deb_path])
        return result.returncode == 0
    finally:
        Path(deb_path).unlink(missing_ok=True)


# ── Step runner ───────────────────────────────────────────────────


def run_install(p: Prose, probe, installer) -> None:
    """Probe → announce → install loop with failure prompt."""
    if probe():
        announce_skip(p)
        return
    announce(p)
    while True:
        if installer():
            print(f"  ✓ {p.name} installed")
            return
        choice = failure_prompt(f"install {p.name}", "command exited non-zero")
        if choice == "s":
            print(f"  ⤳ {p.name} skipped — you will need to install it manually")
            return


# ── Config edits ──────────────────────────────────────────────────


GPG_AGENT_CONF = Path.home() / ".gnupg" / "gpg-agent.conf"
GPG_TTL_LINES = "default-cache-ttl 28800\nmax-cache-ttl 28800\n"

BASHRC = Path.home() / ".bashrc"
BASHRC_GPG_TTY = "export GPG_TTY=$(tty)\n"
BASHRC_KEYCHAIN = 'eval "$(keychain --eval --quiet)"\n'


def configure_gpg_agent_ttl() -> None:
    announce_config(
        "GPG password cache (8 hours)",
        "edits ~/.gnupg/gpg-agent.conf",
        "so you do not re-type your GPG password every commit",
        "after next 'gpgconf --kill gpg-agent' or shell relogin",
    )
    GPG_AGENT_CONF.parent.mkdir(mode=0o700, exist_ok=True)
    existing = GPG_AGENT_CONF.read_text() if GPG_AGENT_CONF.exists() else ""
    if "default-cache-ttl" in existing:
        print("  ✓ already configured")
        return
    sep = "" if (not existing or existing.endswith("\n")) else "\n"
    GPG_AGENT_CONF.write_text(existing + sep + GPG_TTL_LINES)
    print(f"  ✓ wrote {GPG_AGENT_CONF}")


def configure_bashrc() -> None:
    announce_config(
        "shell environment (GPG_TTY + keychain)",
        "appends up to 2 lines to ~/.bashrc",
        "so GPG knows which terminal to prompt on, and SSH/GPG passwords "
        "cache across shell sessions",
        "on next shell open or after 'source ~/.bashrc'",
    )
    existing = BASHRC.read_text() if BASHRC.exists() else ""
    appended = ""
    if "GPG_TTY" not in existing:
        appended += BASHRC_GPG_TTY
    if "keychain --eval" not in existing:
        appended += BASHRC_KEYCHAIN
    if not appended:
        print("  ✓ already configured")
        return
    sep = "" if (not existing or existing.endswith("\n")) else "\n"
    BASHRC.write_text(existing + sep + appended)
    n = appended.count("\n")
    print(f"  ✓ appended {n} line{'s' if n != 1 else ''} to {BASHRC}")


# ── Orchestrator ──────────────────────────────────────────────────


def check_os() -> None:
    if not Path("/etc/debian_version").exists():
        print("This script targets Debian-family Linux (Ubuntu / WSL2 Ubuntu).")
        print("Cross-OS support is tracked in")
        print("  https://github.com/martinhbramwell/ESACP/issues/435")
        sys.exit(1)


UBUNTU_REPO_WHO = (
    "your operating system's own software library — no outside party "
    "is contacted beyond Ubuntu's package mirrors"
)

APT_ITEMS: list[Prose] = [
    Prose(
        name="pinentry-curses",
        what="the in-terminal program that prompts for your GPG password",
        why="so password prompts work inside scripts and remote shells",
        who=UBUNTU_REPO_WHO,
        cost="free, ~200 KB",
    ),
    Prose(
        name="keychain",
        what="a wrapper that keeps your SSH and GPG agents running",
        why="so you type your key passwords once per login, not per command",
        who=UBUNTU_REPO_WHO,
        cost="free, ~150 KB",
    ),
    Prose(
        name="age",
        what="a modern file-encryption tool",
        why="so your passwords and keys can be kept encrypted inside the "
        "code copy, readable only by your machine",
        who=UBUNTU_REPO_WHO,
        cost="free, ~2 MB",
    ),
]

GH_PROSE = Prose(
    name="gh",
    what="GitHub's command-line tool",
    why="so ESACP can manage your code copy on your behalf",
    who="GitHub (the company that hosts your code copy) — they see your "
    "machine downloading their tool over the public internet; they "
    "will not know your name until you sign in, which is a later step",
    cost="free, ~12 MB",
)

SOPS_PROSE = Prose(
    name="sops",
    what="a secrets-encryption tool (originally Mozilla, now CNCF)",
    why="so passwords and keys inside the code copy stay encrypted at rest",
    who="GitHub (where sops is published) — same as above: they see a "
    "download, not an identity",
    cost="free, ~10 MB",
)


def main() -> None:
    print("ESACP on_boarding — controller toolkit installer (v0)")
    print("=" * 56)
    check_os()
    confirm_proceed()
    for p in APT_ITEMS:
        run_install(p, lambda p=p: has_dpkg_pkg(p.name), lambda p=p: install_apt(p.name))
    run_install(GH_PROSE, lambda: has_binary("gh"), install_gh_repo)
    run_install(SOPS_PROSE, lambda: has_binary("sops"), install_sops_deb)
    configure_gpg_agent_ttl()
    configure_bashrc()
    print()
    print("Done. Next steps:")
    print("  1. Close this terminal and open a new one (picks up bashrc).")
    print("     Or run:  source ~/.bashrc")
    print("  2. If you changed gpg-agent.conf for the first time:")
    print("     gpgconf --kill gpg-agent")
    print()


if __name__ == "__main__":
    main()
