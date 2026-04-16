"""Non-VM sections of the lab configuration tree."""

from __future__ import annotations

from rich.tree import Tree

F_HOSTS = "hosts_map.yml"
F_ALL   = "ansible/group_vars/all.yml"
F_KVM   = "ansible/group_vars/kvm.yml"
F_LAB   = "ansible/group_vars/lab.yml"

PORT_MAP = (
    ("Grafana",       "grafana_port"),
    ("Prometheus",    "prometheus_port"),
    ("Loki",          "loki_port"),
    ("Alertmanager",  "alertmanager_port"),
    ("node_exporter", "node_exporter_port"),
)


def _src(rel_path: str) -> str:
    return f"[dim]← {rel_path}[/dim]"


def add_controller(tree: Tree, ctrl: dict) -> None:
    c = tree.add(f"[bold]Controller (this host)[/bold]  {_src(F_HOSTS)}")
    c.add(f"WireGuard  : [cyan]{ctrl.get('wg_ip', '—')}[/cyan]  [spoke]")
    c.add(f"Nickname   : {ctrl.get('nickname', '${HOSTNAME}')}")
    c.add(f"Platform   : {ctrl.get('platform', '—')}")


def add_ssh(tree: Tree, kvm_vars: dict, user: str, key: str) -> None:
    ssh = tree.add(f"[bold]SSH / Ansible[/bold]  {_src(F_KVM)}")
    ssh.add(f"User         : [cyan]{user}[/cyan]")
    ssh.add(f"SSH key      : [dim]{key}[/dim]")
    ssh.add(f"Allowed IPs  : {', '.join(kvm_vars.get('allowed_ssh_ips', []))}")


def add_ports(tree: Tree, all_vars: dict) -> None:
    ports = tree.add(f"[bold]Service Ports[/bold]  {_src(F_ALL)}")
    for svc, key in PORT_MAP:
        ports.add(f"{svc:<14}: [cyan]{all_vars.get(key, '—')}[/cyan]")


def add_alerts(tree: Tree, all_vars: dict) -> None:
    alerts = tree.add("[bold]Alert Profiles[/bold]")
    alerts.add(f"Default : {all_vars.get('alert_profile', '—')}  {_src(F_ALL)}")
    alerts.add(f"KVM lab : [cyan]drill[/cyan]  {_src(F_LAB)}")


def add_system(tree: Tree, all_vars: dict) -> None:
    s = tree.add(f"[bold]System[/bold]  {_src(F_ALL)}")
    s.add(f"Timezone       : {all_vars.get('system_timezone', '—')}")
    s.add(f"Locale         : {all_vars.get('system_locale', '—')}")
    s.add(f"Docker Compose : {all_vars.get('docker_compose_version', '—')}")
