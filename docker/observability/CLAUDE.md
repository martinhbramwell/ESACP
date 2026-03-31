# Observability Stack — Claude Code Context

## Stack

All services in Docker at `/opt/observability/` on saconsole.

| Service | Port | Notes |
|---|---|---|
| Prometheus | 9090 | Jinja2 template — see below |
| Grafana | 3000 | Provisioned dashboards + datasources |
| Loki | 3100 | Wait ~30s before `/ready` returns 200 (GH #47) |
| Alertmanager | 9093 | |
| node_exporter | 9100 | `network_mode: host` + `pid: host`; reached via `host.docker.internal:9100` |
| cAdvisor | 8080 | Pin `v0.55.1` — see below |
| Promtail | — | 3.x required (Docker CE 25+ needs SDK v1.44+) |

Alert profiles: `alerts/` = production (2–10m); `alerts-drill/` = drill (20–30s). KVM hosts → `lab` group → drill.

## Prometheus Configuration

`prometheus.yml` is a **Jinja2 template** (`ansible/roles/observability/templates/prometheus.yml.j2`) — NOT deployed directly from `docker/observability/prometheus/prometheus.yml`.

The Ansible role renders it to the VM. Edit the `.j2` file, not the source copy.
- `host: '{{ inventory_hostname }}'` injected on the `node` scrape job
- `node-target1` job block gated on `{% if 'kvm' in group_names %}`

## Known Gotchas

- **ContainerRestartLoop alert**: use `{name!=""}` filter to exclude cAdvisor's root cgroup entry. (GH #39)
- **Promtail docker_sd_configs**: Docker socket mount required; logs appear under `container_name` not `job`. (GH #40)
- **Promtail systemd-journal**: 3 extra mounts required — `/run/log/journal`, `/var/log/journal`, `/etc/machine-id` (all `:ro`). (GH #41)
- **cAdvisor dashboard template variables**: use concrete metric names in `label_values()` — Grafana 10 blocks `{__name__=~"..."}` selectors. (GH #42)
- **Grafana provisioned dashboards**: `${DS_PROMETHEUS}` not resolved from provisioned files — replace with pinned UID `prometheus`, remove `__inputs` block. (GH #43)
- **cAdvisor Docker SDK**: pin `gcr.io/cadvisor/cadvisor:v0.55.1` — v0.47/v0.49 embed API v1.41, incompatible with Docker CE 25+. (GH #44)
- **Loki `/ready` returns 503 for ~30s** on first start — wait before running `validate_observability.py`. (GH #47)
- **Grafana datasource UIDs**: pinned in `grafana/provisioning/datasources/datasources.yml` as `prometheus` and `loki` — these UIDs must match dashboard JSON references.
