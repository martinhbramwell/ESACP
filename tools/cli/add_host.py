"""addHost — thin CLI dispatcher for host registration.

Wraps ``tools.pipeline.orchestration.host_registration.register_host``.
Restores CLI/UI transport symmetry with ``POST /api/hosts/add``.

Exit codes:
  0 — success
  1 — RuntimeError (infrastructure failure)
  2 — HostRegistrationError (invalid input; HTTP 400 equivalent)
  3 — HostConflictError (already exists; HTTP 409 equivalent)
"""

from __future__ import annotations

from tools.cli._common import PROJECT_ROOT, console, kvm_hosts
from tools.pipeline.orchestration.host_registration import (
    HostConflictError, HostRegistrationError, register_host,
)
from tools.pipeline.orchestration.ip_suggestions import suggest_next_ips


def add_subparser(sub) -> None:
    p = sub.add_parser("addHost", help="Register a new KVM host in hosts_map.yml + regen inventory")
    p.add_argument("hostname", help="DNS/VM name (lowercase, letters/digits/hyphens)")
    p.add_argument("--zone", default="development",
                   choices=("development", "staging", "production"))
    p.add_argument("--vm-role",    dest="vm_role",   default="dev")
    p.add_argument("--wg-ip",      dest="wg_ip",     default=None, help="WG IP (auto-suggested)")
    p.add_argument("--virbr0-ip",  dest="virbr0_ip", default=None, help="virbr0 IP (auto-suggested)")
    p.add_argument("--hypervisor", default=None,     help="Hypervisor alias (default: most-common)")
    p.add_argument("--backend",    default="kvm",
                   choices=("kvm", "vbox", "cloudstack", "vps"))
    p.add_argument("--nickname", default=None, help="Short nickname (default: first 4 chars)")


def run(args, config) -> int:
    suggestions = suggest_next_ips(kvm_hosts(config))
    wg_ip      = args.wg_ip      or suggestions["wg_ip"]
    virbr0_ip  = args.virbr0_ip  or suggestions["virbr0_ip"]
    hypervisor = args.hypervisor or suggestions["hypervisor"]
    nickname   = args.nickname   or ""

    try:
        register_host(
            hostname=args.hostname, nickname=nickname,
            virbr0_ip=virbr0_ip, wg_ip=wg_ip,
            hypervisor=hypervisor, zone=args.zone, vm_role=args.vm_role,
            backend=args.backend, project_root=str(PROJECT_ROOT),
            emit=lambda m: console.print(m),
        )
    except HostConflictError as exc:
        console.print(f"[red]conflict:[/red] {exc}")
        return 3
    except HostRegistrationError as exc:
        console.print(f"[red]invalid:[/red] {exc}")
        return 2
    except RuntimeError as exc:
        console.print(f"[red]error:[/red] {exc}")
        return 1

    console.print(
        f"[green]✓[/green] registered [bold]{args.hostname}[/bold] "
        f"(wg_ip={wg_ip}, virbr0_ip={virbr0_ip}, hypervisor={hypervisor}, "
        f"zone={args.zone}, vm_role={args.vm_role}, backend={args.backend})"
    )
    return 0
