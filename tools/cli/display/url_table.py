"""Build the Rich service-URL table for displayConfiguration."""

from __future__ import annotations

from rich import box
from rich.table import Table

from tools.cli._common import hub_vm, kvm_hosts


def build_url_table(config: dict) -> Table | None:
    hub = hub_vm(config)
    if not hub:
        return None
    hub_ip = kvm_hosts(config)[hub].get("wg_ip", "")
    all_vars = config["all"]
    t = Table(
        title="Service URLs  (WireGuard access from controller)",
        header_style="bold cyan", box=box.SIMPLE,
    )
    t.add_column("Service")
    t.add_column("URL", style="cyan")
    t.add_row("Grafana",      f"http://{hub_ip}:{all_vars.get('grafana_port', 3000)}")
    t.add_row("Prometheus",   f"http://{hub_ip}:{all_vars.get('prometheus_port', 9090)}")
    t.add_row("Alertmanager", f"http://{hub_ip}:{all_vars.get('alertmanager_port', 9093)}")
    for name, info in kvm_hosts(config).items():
        if info.get("wg_role") == "spoke":
            wg_ip = info.get("wg_ip", "")
            t.add_row(
                f"node_exporter ({name})",
                f"http://{wg_ip}:{all_vars.get('node_exporter_port', 9100)}/metrics",
            )
    return t
