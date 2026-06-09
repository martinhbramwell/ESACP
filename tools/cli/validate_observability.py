"""CLI: run the 27-check observability validation suite."""

from __future__ import annotations

import getpass
from pathlib import Path

from tools.cli._common import banner, console, ssh_key_path, vm_user
from tools.pipeline.orchestration.observability_creds import (
    source_grafana_creds, validate_observability,
)


def run(args, config: dict) -> int:
    banner("Validate Observability")
    project_root = Path(__file__).resolve().parent.parent.parent
    script = project_root / "orchestration" / "validate_observability.py"
    if not script.exists():
        console.print(f"[red]❌  Script not found: {script}[/red]")
        return 1

    console.print("Retrieving Grafana credentials...")
    user, password = source_grafana_creds(
        vm_user=vm_user(config), ssh_key=ssh_key_path(),
        emit=console.print,
    )
    if password is None:
        password = getpass.getpass("Grafana admin password: ")

    return validate_observability(user, password, str(script), verbose=args.verbose)
