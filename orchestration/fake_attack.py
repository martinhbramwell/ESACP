#!/usr/bin/env python3
"""
fake_attack.py — Generate controlled SSH failures to exercise the fail2ban → Loki pipeline.

Attack flow:
    1. SSH to target1 (127.0.0.1:2222 via NAT)
    2. From target1, fire ATTACK_COUNT invalid-user SSH attempts at the hub
    3. fail2ban on the hub bans target1's WG IP (port 22 only — monitoring unaffected)
    4. BAN entry written to /var/log/fail2ban.log on the hub
    5. Promtail ships it to Loki  →  job=fail2ban stream exists
    6. Script unbans target1 on the hub

Run from the project root after provisioning and before validation:

    python3 orchestration/fake_attack.py

Requirements: paramiko, rich (see orchestration/requirements.txt)
"""

import os
import sys
import time

import paramiko
from rich.console import Console
from rich.panel import Panel

console = Console()

# ── Config ────────────────────────────────────────────────────────────────────

TARGET1_NAT_HOST  = "127.0.0.1"
TARGET1_NAT_PORT  = 2222
from tools.host_identity import HUB_WG_IP

HUB_LAN_IP       = "192.168.40.50"   # VBox bridged LAN IP — update for KVM
HUB_WG           = HUB_WG_IP
TARGET1_WG_IP     = "10.10.0.3"

ATTACKER_USER     = "fake_attacker"   # must not exist on the hub
SSH_USER          = "you"
SSH_KEY           = os.path.expanduser("~/.ssh/id_ed25519")

ATTACK_COUNT      = 6     # > fail2ban maxretry (5)
POST_BAN_WAIT     = 35    # seconds to let Promtail tail and ship the log entry
BAN_POLL_TIMEOUT  = 30    # seconds to wait for fail2ban to react
BAN_POLL_INTERVAL = 2


# ── SSH helpers ───────────────────────────────────────────────────────────────

def _connect(host, port, user, key):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, key_filename=key, timeout=15)
    return client


def remote_run(host, port, user, key, command):
    """Run command on a remote host; return (stdout, stderr, returncode)."""
    client = _connect(host, port, user, key)
    _, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode()
    err = stderr.read().decode()
    rc  = stdout.channel.recv_exit_status()
    client.close()
    return out, err, rc


# ── Steps ─────────────────────────────────────────────────────────────────────

def ensure_not_pre_banned():
    """If target1's WireGuard IP is already banned on hub, unban it first
    so the attack generates a fresh log entry that Promtail can ship."""
    out, _, _ = remote_run(
        HUB_LAN_IP, 22, SSH_USER, SSH_KEY,
        "sudo fail2ban-client status sshd",
    )
    if TARGET1_WG_IP in out:
        console.print(
            f"[yellow]⚠  {TARGET1_WG_IP} already banned — unbanning first so "
            f"we generate a fresh log entry.[/yellow]"
        )
        remote_run(
            HUB_LAN_IP, 22, SSH_USER, SSH_KEY,
            f"sudo fail2ban-client set sshd unbanip {TARGET1_WG_IP}",
        )
        time.sleep(2)


def generate_attacks():
    """Open a session to target1 and fire ATTACK_COUNT invalid-user SSH attempts
    at hub's WireGuard IP.  The user 'fake_attacker' does not exist on
    hub, so each attempt produces an 'Invalid user' entry in auth.log
    which fail2ban picks up."""
    console.print(
        f"[cyan]Connecting to target1 "
        f"({TARGET1_NAT_HOST}:{TARGET1_NAT_PORT})…[/cyan]"
    )
    client = _connect(TARGET1_NAT_HOST, TARGET1_NAT_PORT, SSH_USER, SSH_KEY)

    console.print(
        f"[cyan]Firing {ATTACK_COUNT} SSH failures  "
        f"target1 ({TARGET1_WG_IP}) → hub ({HUB_WG})…[/cyan]"
    )
    for i in range(1, ATTACK_COUNT + 1):
        # BatchMode=yes — never prompt for password.
        # Connecting as a nonexistent user causes sshd to log
        # "Invalid user fake_attacker from 10.10.0.3" before any key exchange.
        cmd = (
            f"ssh "
            f"-o StrictHostKeyChecking=no "
            f"-o BatchMode=yes "
            f"-o ConnectTimeout=5 "
            f"{ATTACKER_USER}@{HUB_WG} 2>/dev/null; true"
        )
        _, stdout, _ = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        console.print(f"  [dim]attempt {i}/{ATTACK_COUNT} sent[/dim]")

    client.close()
    console.print("[green]✓ Attack sequence complete.[/green]")


def wait_for_ban():
    """Poll hub's fail2ban status until target1's WireGuard IP appears
    in the banned list."""
    console.print(
        f"[cyan]Polling hub for ban of {TARGET1_WG_IP} "
        f"(up to {BAN_POLL_TIMEOUT}s)…[/cyan]"
    )
    deadline = time.time() + BAN_POLL_TIMEOUT
    while time.time() < deadline:
        out, _, _ = remote_run(
            HUB_LAN_IP, 22, SSH_USER, SSH_KEY,
            "sudo fail2ban-client status sshd",
        )
        if TARGET1_WG_IP in out:
            console.print(
                f"[green]✓ Ban confirmed: {TARGET1_WG_IP} in sshd banned list.[/green]"
            )
            return True
        time.sleep(BAN_POLL_INTERVAL)

    console.print(
        f"[red]✗ {TARGET1_WG_IP} was not banned within {BAN_POLL_TIMEOUT}s.[/red]"
    )
    return False


def unban(ip):
    """Remove the ban for ip from hub's sshd jail."""
    console.print(f"[cyan]Unbanning {ip} on hub…[/cyan]")
    out, _, _ = remote_run(
        HUB_LAN_IP, 22, SSH_USER, SSH_KEY,
        f"sudo fail2ban-client set sshd unbanip {ip}",
    )
    console.print(f"[green]✓ Unban response: {out.strip()}[/green]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    console.print(Panel(
        "[bold]ESACP Fake Attack Harness[/bold]\n"
        "Exercises: failed SSH login → fail2ban ban → /var/log/fail2ban.log "
        "→ Promtail → Loki\n"
        f"Attacker : target1 ({TARGET1_WG_IP}) via NAT ({TARGET1_NAT_HOST}:{TARGET1_NAT_PORT})\n"
        f"Victim   : hub ({HUB_WG})",
        style="blue",
    ))

    banned = False
    try:
        ensure_not_pre_banned()
        generate_attacks()

        console.print("[cyan]Waiting 5s for fail2ban to process auth.log…[/cyan]")
        time.sleep(5)

        banned = wait_for_ban()
        if not banned:
            console.print("[red]Aborting — ban not confirmed. Check fail2ban on hub.[/red]")
            sys.exit(1)

        console.print(
            f"[cyan]Waiting {POST_BAN_WAIT}s for Promtail to tail and ship "
            f"the fail2ban.log entry to Loki…[/cyan]"
        )
        time.sleep(POST_BAN_WAIT)

    finally:
        if banned:
            unban(TARGET1_WG_IP)

    console.print(Panel(
        "[green bold]Done.[/green bold]\n"
        "Loki should now have a [bold]job=fail2ban[/bold] stream. "
        "Run validation to confirm:\n\n"
        "[dim]  GRAFANA_ADMIN_USER=admin GRAFANA_ADMIN_PASSWORD=<pw> \\\\\n"
        "  python3 orchestration/validate_observability.py --obs-host 192.168.40.50[/dim]",
        style="green",
    ))


if __name__ == "__main__":
    main()
