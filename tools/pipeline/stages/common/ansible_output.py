"""Ansible-playbook output filter — cross-stage display helper.

Consumed by any dispatcher that streams `ansible-playbook` output and wants
to show only task names + ✓ / ★ / ❌ markers + the final PLAY RECAP.

The returned strings contain Rich markup; callers pipe each non-None return
value into `console.print`. The filter itself does not import Rich — it
only returns strings that happen to carry markup tokens.
"""

from __future__ import annotations

import re
from typing import Optional


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def filter_ansible_line(line: str, state: dict) -> Optional[str]:
    """Return a formatted line to display, or None to suppress.

    ``state`` is a mutable dict the caller preserves across invocations:
    it carries ``current_task``, ``in_recap``, etc.
    """
    clean = strip_ansi(line)

    if clean.startswith("PLAY RECAP"):
        state["in_recap"] = True
        return f"\n[bold cyan]{clean}[/bold cyan]"

    if state.get("in_recap"):
        if re.match(r"\w[\w.\-]+\s*:", clean):
            return f"  [dim]{clean}[/dim]"
        return None

    if clean.startswith("PLAY ["):
        state["current_task"] = ""
        return f"\n[bold cyan]{clean}[/bold cyan]"

    if clean.startswith("TASK ["):
        m = re.match(r"TASK \[(.+?)\]", clean)
        state["current_task"] = m.group(1).strip() if m else clean
        state["task_printed"] = False
        return None

    if clean.startswith("ok:"):
        task = state.get("current_task", "")
        return f"  [green]✓[/green] {task}"

    if clean.startswith("changed:"):
        task = state.get("current_task", "")
        return f"  [yellow]★[/yellow] {task} [yellow](changed)[/yellow]"

    if clean.startswith("skipping:"):
        return None

    if "fatal:" in clean or "FAILED!" in clean or clean.startswith("UNREACHABLE!"):
        return f"[red]❌  {clean}[/red]"

    if state.get("current_task") and re.match(r"\s+(msg|stderr|stdout|reason):", clean):
        return f"[red]{clean}[/red]"

    return None
