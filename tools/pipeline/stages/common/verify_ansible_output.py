#!/usr/bin/env python3
"""Colocated unit test for ansible_output.filter_ansible_line + strip_ansi."""

from __future__ import annotations

import os
import sys

# Replace sys.path[0] (this directory) with PROJECT_ROOT to avoid local
# `types.py` shadowing the stdlib `types` module during import.
sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from tools.pipeline.stages.common.ansible_output import (  # noqa: E402
    filter_ansible_line,
    strip_ansi,
)


def main() -> int:
    # strip_ansi removes CSI color codes
    assert strip_ansi("\x1b[32mhello\x1b[0m world") == "hello world"
    assert strip_ansi("plain") == "plain"

    # filter_ansible_line drives its own state dict across calls
    state: dict = {"current_task": "", "in_recap": False}

    assert filter_ansible_line("PLAY [base-all] ***", state) == "\n[bold cyan]PLAY [base-all] ***[/bold cyan]"
    assert filter_ansible_line("TASK [install pkg] ***", state) is None
    assert state["current_task"] == "install pkg"
    assert filter_ansible_line("ok: [dev01]", state) == "  [green]✓[/green] install pkg"
    assert filter_ansible_line("changed: [dev01]", state) == "  [yellow]★[/yellow] install pkg [yellow](changed)[/yellow]"
    assert filter_ansible_line("skipping: [dev01]", state) is None
    assert filter_ansible_line("fatal: [dev01]: FAILED!", state) == "[red]❌  fatal: [dev01]: FAILED![/red]"

    # PLAY RECAP flips recap mode and only summary lines pass through
    assert filter_ansible_line("PLAY RECAP ***", state).startswith("\n[bold cyan]PLAY RECAP")
    assert state["in_recap"] is True
    assert filter_ansible_line("dev01                      : ok=77  changed=11", state) == "  [dim]dev01                      : ok=77  changed=11[/dim]"
    assert filter_ansible_line("unrelated line", state) is None

    print("ansible_output: all asserts passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
