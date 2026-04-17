"""Install missing apt packages interactively."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence

from tools.pipeline.stages.common.types import Emit


def apt_install(packages: Sequence[str], emit: Emit) -> bool:
    """Run ``sudo apt install -y <packages>``. Returns True on success."""
    if not packages:
        return True
    r = subprocess.run(["sudo", "apt", "install", "-y", *sorted(packages)])
    if r.returncode != 0:
        emit("[red]❌  apt install failed.[/red]")
        return False
    emit("[green]✅  Packages installed.[/green]")
    return True
