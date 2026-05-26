#!/usr/bin/env python3
"""ESACP unified lab management CLI.

Thin argparse + dispatch layer; business logic lives in ``tools/cli/`` and
``tools/pipeline/`` per CLAUDE.md anti-spiral rules. Use ``--help`` for the
subcommand list.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.cli import (
    add_host, apply_substrate_migration, apply_v16_post_migrate_fixups,
    build_vm, clear_known_hosts, confirm_prerequisites, destroy, destroy_vm,
    display_configuration, provision, provision_generic, provision_vm,
    snapshot_vm, validate_keys, validate_observability, verify_vpn,
)
from tools.cli._common import console, load_config, kvm_hosts


DISPATCH = {
    "confirmPrerequisites":  confirm_prerequisites.run,
    "validateKeys":          validate_keys.run,
    "clearKnownHosts":       clear_known_hosts.run,
    "addHost":               add_host.run,
    "destroyVM":             destroy_vm.run,
    "buildVM":               build_vm.run,
    "provisionVM":           provision_vm.run,
    "provision":             provision.run,
    "provisionGeneric":      provision_generic.run,
    "destroy":               destroy.run,
    "verifyVPN":             verify_vpn.run,
    "validateObservability": validate_observability.run,
    "snapShotVM":            snapshot_vm.run,
    "displayConfiguration":  display_configuration.run,
    "applySubstrateMigration": apply_substrate_migration.run,
    "applyV16PostMigrateFixups": apply_v16_post_migrate_fixups.run,
}

VM_COMMANDS = {"destroyVM", "buildVM", "provisionVM", "provision", "provisionGeneric", "destroy", "snapShotVM", "applySubstrateMigration", "applyV16PostMigrateFixups"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ESACP unified lab management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", metavar="<subcommand>", required=True)
    sub.add_parser("confirmPrerequisites", help="Check and install required host software")
    sub.add_parser("validateKeys",         help="Verify SOPS/age keys and WireGuard key structure")
    sub.add_parser("clearKnownHosts",      help="Remove stale SSH known_hosts entries for ESACP VMs")

    for mod in (add_host, provision_generic, apply_substrate_migration, apply_v16_post_migrate_fixups):
        mod.add_subparser(sub)

    for name, help_text in (
        ("destroyVM",   "Destroy a KVM VM and all its storage"),
        ("buildVM",     "Build seed ISO, create VM, wait for autoinstall"),
        ("provision",   "Full pipeline: create VM + provision + differentiate (stages 1–9)"),
        ("destroy",     "Full teardown: VM + WireGuard + hosts_map + SOPS keys"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("vm", help="VM name")

    p = sub.add_parser("provisionVM", help="Run Ansible provisioning (task names and errors only)")
    p.add_argument("vm")
    p.add_argument("--check", action="store_true", help="Ansible dry run")
    p.add_argument("--skip-fresh-snapshot", action="store_true", help="Skip 'Fresh Install' snapshot step")

    sub.add_parser("verifyVPN", help="Test WireGuard connectivity and inter-VM routing")

    p = sub.add_parser("validateObservability", help="Run the 27-check observability validation suite")
    p.add_argument("--verbose", "-v", action="store_true", help="Show passing check details")

    p = sub.add_parser("snapShotVM", help="Create a snapshot or list snapshots for a VM")
    p.add_argument("vm")
    p.add_argument("name", nargs="?", help="Snapshot name (omit to list existing)")

    sub.add_parser("displayConfiguration", help="Show the lab configuration tree")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        config = load_config()
    except FileNotFoundError as exc:
        print(f"Config file not found: {exc}", file=sys.stderr)
        print("Run from the project root, or ensure hosts_map.yml exists.", file=sys.stderr)
        return 1

    if args.command in VM_COMMANDS and hasattr(args, "vm"):
        valid = list(kvm_hosts(config).keys())
        if args.vm not in valid:
            console.print(f"[red]Unknown VM '{args.vm}'. Valid: {', '.join(valid)}[/red]")
            return 1

    return DISPATCH[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
