#!/usr/bin/env python3
"""
validate_observability.py — ESACP observability stack end-to-end validation

Checks that all services are healthy and correctly wired to Grafana.
Run from the controller host against a deployed observability stack.

All hostnames, scrape jobs, datasource UIDs, and dashboard titles are derived
from the project's own config files — nothing is hardcoded in this script.

Usage:
    python orchestration/validate_observability.py [--obs-host NAME] [--verbose]

    --obs-host  Name of the host running the observability stack as it appears
                in hosts_map.yml (default: auto-detected — first reachable
                wg_role=hub host; works across KVM and VBox platforms).

Credentials (Grafana):
    Export GRAFANA_ADMIN_USER and GRAFANA_ADMIN_PASSWORD before running,
    or pass --grafana-user / --grafana-password on the command line.

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import argparse
import base64
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ── Project layout ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent

HOSTS_MAP       = PROJECT_ROOT / "hosts_map.yml"
PROMETHEUS_CFG  = PROJECT_ROOT / "docker/observability/prometheus/prometheus.yml"
PROMTAIL_CFG    = PROJECT_ROOT / "docker/observability/promtail/promtail.yml"
DATASOURCES_CFG = PROJECT_ROOT / "docker/observability/grafana/provisioning/datasources/datasources.yml"
DASHBOARDS_DIR  = PROJECT_ROOT / "docker/observability/grafana/provisioning/dashboards/json"


# ── Config readers ────────────────────────────────────────────────────────────

def load_hosts_map() -> dict:
    with open(HOSTS_MAP) as f:
        return yaml.safe_load(f)


def _tcp_reachable(host: str, port: int = 22, timeout: float = 1.0) -> bool:
    """Return True if a TCP connection to host:port succeeds within timeout."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def find_obs_host(hosts_map: dict, name: Optional[str]) -> tuple[str, str]:
    """
    Return (hostname, ip) for the observability host.

    Resolution order (named):
      1. Exact key match in any group of hosts_map.yml
      2. Nickname match
      3. Treat as literal hostname/IP

    Resolution order (auto-detect):
      Collect all ansible_managed wg_role=hub hosts from every group, then
      return the first one reachable on port 22 (SSH). This works correctly
      across platforms: on KVM the virbr0 IP is probed; on VBox the hostname
      ('saconsole') resolves via /etc/hosts to the bridged LAN IP.
      Falls back to the first candidate if none respond (stack may be down).
    """
    def ip_for(attrs: dict) -> str:
        return attrs.get("virbr0_ip") or attrs.get("ansible_host") or attrs.get("hostname", "")

    # Build a flat view for named lookups (last-writer-wins per key is fine here
    # because named lookups check nickname/key directly).
    all_hosts: dict[str, dict] = {}
    for group_hosts in hosts_map.get("groups", {}).values():
        if isinstance(group_hosts, dict):
            for hname, attrs in group_hosts.items():
                if isinstance(attrs, dict):
                    all_hosts[hname] = attrs

    if name:
        if name in all_hosts:
            return name, ip_for(all_hosts[name])
        for hname, attrs in all_hosts.items():
            if attrs.get("nickname") == name:
                return hname, ip_for(attrs)
        return name, name  # treat as literal hostname/IP

    # auto-detect: gather all hub hosts across all groups (preserves duplicates
    # across groups, unlike the flat all_hosts dict).
    candidates: list[tuple[str, str]] = []
    for group_hosts in hosts_map.get("groups", {}).values():
        if not isinstance(group_hosts, dict):
            continue
        for hname, attrs in group_hosts.items():
            if (isinstance(attrs, dict)
                    and attrs.get("ansible_managed")
                    and attrs.get("wg_role") == "hub"):
                candidates.append((hname, ip_for(attrs)))

    for hname, ip in candidates:
        if _tcp_reachable(ip):
            return hname, ip

    if candidates:
        # Nothing reachable — return first candidate so error messages are useful.
        return candidates[0]

    raise SystemExit("Could not auto-detect observability host. Use --obs-host.")


def load_expected_jobs() -> list[str]:
    with open(PROMETHEUS_CFG) as f:
        cfg = yaml.safe_load(f)
    return [job["job_name"] for job in cfg.get("scrape_configs", [])
            if not job["job_name"].startswith("#")]


def load_datasource_uids() -> list[str]:
    with open(DATASOURCES_CFG) as f:
        cfg = yaml.safe_load(f)
    return [ds["uid"] for ds in cfg.get("datasources", []) if "uid" in ds]


def load_promtail_loki_jobs() -> tuple[list[str], bool]:
    """
    Parse promtail.yml and return:
      (static_job_names, has_docker_sd)

    static_job_names — job_name values from scrape_configs that use static_configs
                       or journal/file sources (these produce job=<name> labels in Loki)
    has_docker_sd    — True if any scrape_config uses docker_sd_configs
                       (those produce container_name labels, not job=<name>)
    """
    with open(PROMTAIL_CFG) as f:
        cfg = yaml.safe_load(f)
    static_jobs = []
    has_docker_sd = False
    for sc in cfg.get("scrape_configs", []):
        if "docker_sd_configs" in sc:
            has_docker_sd = True
        else:
            static_jobs.append(sc["job_name"])
    return static_jobs, has_docker_sd


def load_dashboard_titles() -> list[str]:
    titles = []
    for p in sorted(DASHBOARDS_DIR.glob("*.json")):
        try:
            with open(p) as f:
                d = json.load(f)
            title = d.get("title", "")
            if title:
                titles.append(title)
        except Exception:
            pass
    return titles


def load_monitored_nodenames(hosts_map: dict) -> list[str]:
    """Return hostnames of all ansible_managed hosts that have a wg_ip (i.e. monitored)."""
    names = []
    for group_hosts in hosts_map.get("groups", {}).values():
        if not isinstance(group_hosts, dict):
            continue
        for hname, attrs in group_hosts.items():
            if isinstance(attrs, dict) and attrs.get("ansible_managed") and attrs.get("wg_ip"):
                # controller (localhost) is not monitored, skip
                if attrs.get("ansible_connection") == "local":
                    continue
                names.append(hname)
    return names


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _request(url: str, *, method: str = "GET", data: bytes = None,
             headers: dict = None, timeout: int = 10):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            ct = resp.headers.get_content_type() or ""
            if "json" in ct:
                return json.loads(body) if body.strip() else {}
            return body.decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if body.strip():
            try:
                return json.loads(body)
            except Exception:
                pass
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {body.strip() or '(empty body)'}")


def get(url: str, headers: dict = None, timeout: int = 10):
    return _request(url, headers=headers, timeout=timeout)


def grafana_auth(user: str, password: str) -> dict:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


# ── Check result ──────────────────────────────────────────────────────────────

class Check:
    def __init__(self, name: str, passed: bool, detail: str = ""):
        self.name = name
        self.passed = passed
        self.detail = detail

    @property
    def status(self) -> str:
        return "[green]PASS[/green]" if self.passed else "[red]FAIL[/red]"


# ── Individual checks ─────────────────────────────────────────────────────────

def check_grafana_health(base: str) -> Check:
    try:
        r = get(f"{base}/api/health")
        ok = isinstance(r, dict) and r.get("database") == "ok"
        detail = f"database={r.get('database')}  version={r.get('version')}" if ok else str(r)
        return Check("Grafana /api/health", ok, detail)
    except Exception as e:
        return Check("Grafana /api/health", False, str(e))


def check_prometheus_health(base: str) -> Check:
    try:
        r = get(f"{base}/-/ready")
        ok = isinstance(r, str) and "ready" in r.lower()
        return Check("Prometheus /-/ready", ok, r.strip() if isinstance(r, str) else str(r))
    except Exception as e:
        return Check("Prometheus /-/ready", False, str(e))


def check_loki_health(base: str) -> Check:
    try:
        r = get(f"{base}/ready")
        ok = isinstance(r, str) and "ready" in r.lower()
        return Check("Loki /ready", ok, r.strip() if isinstance(r, str) else str(r))
    except Exception as e:
        return Check("Loki /ready", False, str(e))


def check_alertmanager_health(base: str) -> Check:
    try:
        r = get(f"{base}/api/v2/status")
        ok = isinstance(r, dict) and r.get("cluster", {}).get("status") == "ready"
        detail = (f"cluster={r.get('cluster', {}).get('status')}"
                  if isinstance(r, dict) else str(r))
        return Check("Alertmanager /api/v2/status", ok, detail)
    except Exception as e:
        return Check("Alertmanager /api/v2/status", False, str(e))


def check_prometheus_targets(prom_base: str, expected_jobs: list[str]) -> list[Check]:
    checks = []
    try:
        r = get(f"{prom_base}/api/v1/targets")
        active = r.get("data", {}).get("activeTargets", [])
        by_job: dict[str, list] = {}
        for t in active:
            j = t.get("labels", {}).get("job", "")
            by_job.setdefault(j, []).append(t)

        for job in expected_jobs:
            targets = by_job.get(job, [])
            if not targets:
                checks.append(Check(f"  job/{job}", False, "not found in active targets"))
                continue
            all_up = all(t.get("health") == "up" for t in targets)
            detail = (", ".join(t.get("scrapeUrl", "?") for t in targets) if all_up
                      else str([t.get("health") for t in targets]))
            checks.append(Check(f"  job/{job}", all_up, detail))
    except Exception as e:
        for job in expected_jobs:
            checks.append(Check(f"  job/{job}", False, str(e)))
    return checks


def check_metric(prom_base: str, label: str, query: str) -> Check:
    url = f"{prom_base}/api/v1/query?query={urllib.parse.quote(query)}"
    try:
        r = get(url)
        results = r.get("data", {}).get("result", [])
        ok = len(results) > 0
        if ok:
            val = results[0].get("value", ["", "?"])[1]
            metric = results[0].get("metric", {})
            detail = f"value={val}  {metric}"
        else:
            detail = "no series returned"
        return Check(f"  {label}", ok, detail)
    except Exception as e:
        return Check(f"  {label}", False, str(e))


def check_loki_labels(loki_base: str) -> Check:
    try:
        r = get(f"{loki_base}/loki/api/v1/labels")
        labels = r.get("data", []) if isinstance(r, dict) else []
        ok = len(labels) > 0
        return Check("Loki /loki/api/v1/labels", ok,
                     f"labels={labels}" if ok else "no labels — no logs ingested yet")
    except Exception as e:
        return Check("Loki /loki/api/v1/labels", False, str(e))


def check_loki_container_names(loki_base: str) -> Check:
    """Verify Docker container logs are flowing (docker_sd_configs sets container_name, not job)."""
    try:
        r = get(f"{loki_base}/loki/api/v1/label/container_name/values")
        names = r.get("data", []) if isinstance(r, dict) else []
        ok = len(names) > 0
        return Check("  Loki docker (container_name values)", ok,
                     f"{names}" if ok else "no container_name values — Docker logs not ingested")
    except Exception as e:
        return Check("  Loki docker (container_name values)", False, str(e))


def check_loki_job(loki_base: str, job: str) -> Check:
    query = urllib.parse.quote(f'{{job="{job}"}}')
    # Query the last hour; Loki requires nanosecond timestamps
    end_ns   = int(time.time()) * 10**9
    start_ns = end_ns - 3600 * 10**9
    url = (f"{loki_base}/loki/api/v1/query_range"
           f"?query={query}&limit=1&start={start_ns}&end={end_ns}")
    try:
        r = get(url)
        streams = r.get("data", {}).get("result", [])
        ok = len(streams) > 0
        return Check(f"  Loki job={job}", ok,
                     f"{len(streams)} stream(s)" if ok else "no streams (logs not yet ingested)")
    except Exception as e:
        return Check(f"  Loki job={job}", False, str(e))


def check_grafana_datasource_health(grafana_base: str, uid: str, auth: dict) -> Check:
    try:
        r = get(f"{grafana_base}/api/datasources/uid/{uid}/health", headers=auth)
        ok = isinstance(r, dict) and r.get("status") == "OK"
        return Check(f"  datasource uid={uid}", ok, r.get("message", str(r)))
    except Exception as e:
        return Check(f"  datasource uid={uid}", False, str(e))


def check_grafana_dashboards(grafana_base: str, auth: dict,
                              expected_titles: list[str]) -> list[Check]:
    checks = []
    try:
        boards = get(f"{grafana_base}/api/search?type=dash-db", headers=auth)
        provisioned = [b.get("title", "") for b in boards]
        provisioned_lower = [t.lower() for t in provisioned]
        for title in expected_titles:
            found = title.lower() in provisioned_lower
            checks.append(Check(f"  dashboard '{title}'", found,
                                "provisioned" if found else
                                f"not found (have: {provisioned})"))
    except Exception as e:
        for title in expected_titles:
            checks.append(Check(f"  dashboard '{title}'", False, str(e)))
    return checks


# ── Report helpers ────────────────────────────────────────────────────────────

def render_section(title: str, checks: list[Check], verbose: bool) -> None:
    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    table.add_column("status", width=6)
    table.add_column("name")
    table.add_column("detail", style="dim")
    for c in checks:
        if not c.passed or verbose:
            table.add_row(c.status, c.name, c.detail)
        else:
            table.add_row(c.status, c.name, "")
    console.print(f"\n[bold]{title}[/bold]")
    console.print(table)


def render_summary(all_checks: list[Check]) -> bool:
    total  = len(all_checks)
    passed = sum(1 for c in all_checks if c.passed)
    failed = total - passed
    colour = "green" if failed == 0 else "red"
    label  = "ALL CHECKS PASSED" if failed == 0 else f"{failed} CHECK(S) FAILED"
    console.print(Panel(
        f"[bold {colour}]{label}[/bold {colour}]  [dim]({passed}/{total} passed)[/dim]",
        expand=False,
    ))
    return failed == 0


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the ESACP observability stack end-to-end.")
    parser.add_argument(
        "--obs-host", default=None,
        help="Name/nickname from hosts_map.yml of the host running the observability stack "
             "(default: auto-detected — first reachable wg_role=hub host across all platform groups)")
    parser.add_argument(
        "--grafana-user",
        default=os.environ.get("GRAFANA_ADMIN_USER", "admin"),
        help="Grafana admin username (env: GRAFANA_ADMIN_USER)")
    parser.add_argument(
        "--grafana-password",
        default=os.environ.get("GRAFANA_ADMIN_PASSWORD", ""),
        help="Grafana admin password (env: GRAFANA_ADMIN_PASSWORD)")
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detail lines for passing checks too")
    args = parser.parse_args()

    if not args.grafana_password:
        console.print(
            "[red]Error:[/red] Grafana password not set.\n"
            "  Export [bold]GRAFANA_ADMIN_PASSWORD[/bold] or use --grafana-password.")
        return 1

    # ── Load config ────────────────────────────────────────────────────────────
    hosts_map             = load_hosts_map()
    obs_hostname, obs_ip  = find_obs_host(hosts_map, args.obs_host)
    expected_jobs         = load_expected_jobs()
    ds_uids               = load_datasource_uids()
    dash_titles           = load_dashboard_titles()
    nodenames             = load_monitored_nodenames(hosts_map)
    loki_static_jobs, has_docker_sd = load_promtail_loki_jobs()

    grafana  = f"http://{obs_ip}:3000"
    prom     = f"http://{obs_ip}:9090"
    loki     = f"http://{obs_ip}:3100"
    alertmgr = f"http://{obs_ip}:9093"
    auth     = grafana_auth(args.grafana_user, args.grafana_password)

    console.print(Panel(
        f"[bold]ESACP Observability Validation[/bold]\n"
        f"[dim]obs host : {obs_hostname}  ({obs_ip})\n"
        f"grafana  : {grafana}\n"
        f"jobs     : {', '.join(expected_jobs)}\n"
        f"nodes    : {', '.join(nodenames)}[/dim]",
        expand=False,
    ))

    all_checks: list[Check] = []

    # ── 1. Service health ──────────────────────────────────────────────────────
    health = [
        check_grafana_health(grafana),
        check_prometheus_health(prom),
        check_loki_health(loki),
        check_alertmanager_health(alertmgr),
    ]
    render_section("1. Service health", health, args.verbose)
    all_checks.extend(health)

    # ── 2. Prometheus targets ──────────────────────────────────────────────────
    targets = check_prometheus_targets(prom, expected_jobs)
    render_section(
        f"2. Prometheus scrape targets ({len(expected_jobs)} jobs, all must be UP)",
        targets, args.verbose)
    all_checks.extend(targets)

    # ── 3. Key metric spot-checks ──────────────────────────────────────────────
    metrics = []
    for node in nodenames:
        metrics.append(check_metric(
            prom, f"node_uname_info nodename={node}",
            f'node_uname_info{{nodename="{node}"}}'))
    metrics.append(check_metric(
        prom, "cAdvisor: container_cpu_usage_seconds_total present",
        'count(container_cpu_usage_seconds_total{name!=""})'))
    # saconsole's node_exporter runs on host.docker.internal:9100 (network_mode: host)
    metrics.append(check_metric(
        prom, f"wg0 visible on {obs_hostname}",
        f'node_network_info{{device="wg0",instance="host.docker.internal:9100"}}'))
    render_section("3. Key metric spot-checks", metrics, args.verbose)
    all_checks.extend(metrics)

    # ── 4. Loki log ingestion ──────────────────────────────────────────────────
    loki_checks = [check_loki_labels(loki)]
    for job in loki_static_jobs:        # static scrape jobs → job=<name> label
        loki_checks.append(check_loki_job(loki, job))
    if has_docker_sd:                   # docker_sd → container_name label, not job
        loki_checks.append(check_loki_container_names(loki))
    render_section(
        f"4. Loki log ingestion ({len(loki_static_jobs)} static jobs"
        + (", docker container_name" if has_docker_sd else "") + ")",
        loki_checks, args.verbose)
    all_checks.extend(loki_checks)

    # ── 5. Grafana datasource health ───────────────────────────────────────────
    ds_checks = [check_grafana_datasource_health(grafana, uid, auth)
                 for uid in ds_uids]
    render_section(
        f"5. Grafana datasource health ({len(ds_uids)} datasources with UIDs)",
        ds_checks, args.verbose)
    all_checks.extend(ds_checks)

    # ── 6. Grafana dashboards provisioned ─────────────────────────────────────
    dash_checks = check_grafana_dashboards(grafana, auth, dash_titles)
    render_section(
        f"6. Grafana dashboards provisioned ({len(dash_titles)} expected)",
        dash_checks, args.verbose)
    all_checks.extend(dash_checks)

    # ── Summary ────────────────────────────────────────────────────────────────
    console.print()
    return 0 if render_summary(all_checks) else 1


if __name__ == "__main__":
    sys.exit(main())
