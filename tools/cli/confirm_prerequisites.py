"""CLI: confirm host prerequisites (tools + files)."""

from __future__ import annotations

from pathlib import Path

from tools.cli._common import banner, confirm, console, ssh_key_path
from tools.pipeline.stages.preflight.apt_install import apt_install
from tools.pipeline.stages.preflight.check_files import check_files
from tools.pipeline.stages.preflight.check_tools import (
    MANUAL_INSTALL_HINTS, check_tools,
)


def run(args, config: dict) -> int:
    banner("Confirm Prerequisites")
    project_root = str(Path(__file__).resolve().parent.parent.parent)

    console.print("[bold cyan]Tool checks[/bold cyan]")
    tool_status = check_tools(emit=console.print)

    console.print()
    console.print("[bold cyan]File checks[/bold cyan]")
    file_results = check_files(project_root, ssh_key_path(config), emit=console.print)
    file_issues = [(p, d) for p, d, exists in file_results if not exists]

    console.print()
    if not tool_status.missing_apt and not tool_status.missing_manual and not file_issues:
        console.print("[green]✅  All prerequisites satisfied.[/green]")
        return 0

    if tool_status.missing_apt:
        pkgs = " ".join(sorted(tool_status.missing_apt))
        console.print(f"[yellow]Missing apt packages:[/yellow] {pkgs}")
        if confirm("Install now via apt?"):
            if not apt_install(sorted(tool_status.missing_apt), console.print):
                return 1
        else:
            console.print(f"[dim]Re-run after: sudo apt install -y {pkgs}[/dim]")

    if tool_status.missing_manual:
        console.print()
        console.print("[yellow]Manual installs required:[/yellow]")
        reported: set[str] = set()
        for tool, pkg in tool_status.missing_manual:
            if pkg in reported:
                continue
            hint = MANUAL_INSTALL_HINTS.get(tool, MANUAL_INSTALL_HINTS.get(pkg, ""))
            console.print(f"  [cyan]{pkg}[/cyan]: {hint}")
            reported.add(pkg)

    if file_issues:
        console.print()
        console.print("[yellow]Missing files:[/yellow]")
        ssh_key = Path(ssh_key_path(config))
        for path, desc in file_issues:
            if "age/keys.txt" in str(path):
                console.print(f"  age key: age-keygen -o {path}")
                console.print("           then add the public key as a recipient in .sops.yaml")
            elif ".pub" in str(path):
                console.print(f"  SSH public key: ssh-keygen -y -f {ssh_key} > {path}")
            elif ssh_key.name in str(path):
                console.print(f"  SSH key: generate with ssh-keygen -t ed25519 -f {path}")
            else:
                console.print(f"  {desc}: {path} — see SETUP_GUIDE.md")

    return 1 if (tool_status.missing_manual or file_issues) else 0
