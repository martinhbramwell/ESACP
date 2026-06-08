"""provisionGeneric — thin CLI dispatcher for skeletal ERPNext + wizard.

Wraps ``tools.pipeline.macro.provision_generic.run`` (stages 1-9) and
``tools.pipeline.orchestration.wizard_run.run_wizard`` (record/replay/existing).
Restores CLI/UI transport symmetry with ``POST /api/provision/erpnext-generic``.

Exit codes:
  0 — success
  1 — RuntimeError / CalledProcessError / hub rejected / no virbr0_ip
  2 — invalid args (wizard_mode, missing wizard-arg for replay/existing)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.cli._common import banner, console, kvm_hosts
from tools.host_identity import ZONE_DOMAINS
from tools.pipeline.macro.provision_generic import run as run_macro
from tools.pipeline.orchestration.wizard_run import run_wizard

_WIZARD_MODES = ("record", "replay", "existing", "none")


def add_subparser(sub) -> None:
    p = sub.add_parser("provisionGeneric",
        help="Skeletal ERPNext pipeline (stages 1-9) + setup wizard (record/replay/existing)")
    p.add_argument("vm", help="VM name")
    p.add_argument("--wizard-mode", dest="wizard_mode", default="record",
                   choices=_WIZARD_MODES,
                   help="record = capture new Playwright script; replay = run existing script; "
                        "existing = restore from golden backup; none = skip the wizard "
                        "(headless stages-1-9 rebuild, e.g. template acceptance)")
    p.add_argument("--wizard-arg", dest="wizard_arg", default="",
                   help="Script filename (replay) or backup filename (existing); required for those modes")


def run(args, config: dict) -> int:
    if args.wizard_mode in ("replay", "existing") and not args.wizard_arg:
        console.print(f"[red]--wizard-arg required when --wizard-mode={args.wizard_mode}[/red]")
        return 2

    hostname = args.vm
    banner(f"Provision Generic: {hostname} (wizard={args.wizard_mode})")

    vm_info = kvm_hosts(config).get(hostname, {})
    virbr0_ip = vm_info.get("virbr0_ip")
    if not virbr0_ip:
        console.print(f"[red]No virbr0_ip for '{hostname}' in hosts_map.yml[/red]")
        return 1
    if vm_info.get("wg_role") == "hub":
        console.print(f"[red]Cannot provision hub node '{hostname}' — use rebuild_lab.sh[/red]")
        return 1

    project_root = Path(__file__).resolve().parent.parent.parent
    zone = next(
        (g for g in vm_info.get("ansible_groups", [])
         if g in ("production", "staging", "development")),
        "development",
    )
    domain = ZONE_DOMAINS.get(zone, "iridium.blue")
    site_url = f"https://{hostname}.{domain}"

    try:
        run_macro(hostname=hostname, virbr0_ip=virbr0_ip,
                  project_root=str(project_root), emit=console.print)
        run_wizard(mode=args.wizard_mode, hostname=hostname, site_url=site_url,
                   arg=args.wizard_arg, project_root=project_root, emit=console.print)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        console.print(f"[red]Pipeline failed: {exc}[/red]")
        return 1

    console.print()
    console.print(f"[green]Generic provision complete — {site_url}[/green]")
    return 0
