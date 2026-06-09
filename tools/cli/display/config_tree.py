"""Build the Rich configuration tree for displayConfiguration."""

from __future__ import annotations

from rich.tree import Tree

from tools.cli._common import (
    controller_info, kvm_hosts, ssh_key_path, vm_user,
)
from tools.cli.display._meta_sections import (
    add_alerts, add_controller, add_ports, add_ssh, add_system,
)

F_HOSTS = "hosts_map.yml"
F_ALL   = "ansible/group_vars/all.yml"
F_KEYS  = "config/wireguard/keys.sops.yml"


def _src(rel_path: str) -> str:
    return f"[dim]← {rel_path}[/dim]"


def build_tree(config: dict) -> Tree:
    hosts_map, all_vars, kvm_vars = config["hosts"], config["all"], config["kvm"]
    tree = Tree("[bold cyan]ESACP[/bold cyan]")
    _add_wireguard(tree, hosts_map, all_vars)
    _add_vms(tree, kvm_hosts(config))
    add_controller(tree, controller_info(config))
    add_ssh(tree, kvm_vars, vm_user(config), ssh_key_path())
    add_ports(tree, all_vars)
    add_alerts(tree, all_vars)
    add_system(tree, all_vars)
    return tree


def _add_wireguard(tree: Tree, hosts_map: dict, all_vars: dict) -> None:
    wg = tree.add(f"[bold]WireGuard Network[/bold]  {_src(F_HOSTS)}")
    wg.add(f"Subnet  : [cyan]{hosts_map.get('wireguard_subnet', '—')}[/cyan]")
    wg.add(f"Port    : [cyan]{hosts_map.get('wireguard_port', '—')}[/cyan]  (UDP)")
    pubkeys = wg.add(f"Public keys  {_src(F_ALL)}")
    for var, val in all_vars.items():
        if var.startswith("wg_pubkey_"):
            pubkeys.add(f"{var.removeprefix('wg_pubkey_'):<12}: [dim]{val}[/dim]")
    wg.add(f"Private keys / PSKs  {_src(F_KEYS)}").add(
        "[dim](SOPS/age encrypted — run validateKeys to verify)[/dim]")


def _add_vms(tree: Tree, hosts: dict) -> None:
    vms = tree.add(f"[bold]KVM VMs[/bold]  {_src(F_HOSTS)}")
    for name, info in hosts.items():
        role = info.get("wg_role", "spoke")
        v = vms.add(f"[bold green]{name}[/bold green]  ({info.get('nickname', '')})  [[dim]{role}[/dim]]")
        v.add(f"virbr0 IP  : [cyan]{info.get('virbr0_ip', '—')}[/cyan]")
        v.add(f"WireGuard  : [cyan]{info.get('wg_ip', '—')}[/cyan]")
        v.add(f"Groups     : {', '.join(info.get('ansible_groups', []))}")
        v.add(f"Platform   : {info.get('platform', '—')}")
