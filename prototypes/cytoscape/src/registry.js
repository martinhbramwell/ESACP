// registry.js — recursive drill-down data registry
//
// Each entry: { label, fetch: async () => { nodes, edges }, children: { ... } }
// fetch() returns the graph data for that level.
// children keys must match node IDs returned by the parent's fetch().
//
// Network note: live API calls require the browser to reach saconsole's ports.
// From WSL/Windows (Platform 1), the KVM network is unreachable — fallback data
// is used automatically. From Xubuntu (Platform 2), live calls will succeed
// provided CORS headers are present. Add a Vite proxy in vite.config.js to work
// around CORS without touching the VMs.

const SACONSOLE  = 'http://192.168.122.10'
const PROMETHEUS = `${SACONSOLE}:9090`
const DOCKER_API = `${SACONSOLE}:8088`   // future saconsole REST bridge; not live yet

// ── Fallback static data ───────────────────────────────────────────────────
// Realistic snapshots used when the live API is unreachable.

const FALLBACK = {

  saconsole_containers: {
    nodes: [
      { data: { id: 'grafana',       label: 'grafana',       image: 'grafana/grafana:10.2.3',            status: 'Up', state: 'running', ports: '3000' } },
      { data: { id: 'prometheus',    label: 'prometheus',    image: 'prom/prometheus:v2.48.1',           status: 'Up', state: 'running', ports: '9090' } },
      { data: { id: 'alertmanager',  label: 'alertmanager',  image: 'prom/alertmanager:v0.26.0',         status: 'Up', state: 'running', ports: '9093' } },
      { data: { id: 'loki',          label: 'loki',          image: 'grafana/loki:2.9.3',               status: 'Up', state: 'running', ports: '3100' } },
      { data: { id: 'promtail',      label: 'promtail',      image: 'grafana/promtail:3.3.2',           status: 'Up', state: 'running', ports: '9080' } },
      { data: { id: 'node_exporter', label: 'node_exporter', image: 'prom/node-exporter:v1.7.0',        status: 'Up', state: 'running', ports: '9100', network: 'host' } },
      { data: { id: 'cadvisor',      label: 'cadvisor',      image: 'gcr.io/cadvisor/cadvisor:v0.55.1', status: 'Up', state: 'running', ports: '8080' } },
    ],
    edges: [
      { data: { source: 'prometheus',   target: 'node_exporter', label: 'scrape' } },
      { data: { source: 'prometheus',   target: 'cadvisor',      label: 'scrape' } },
      { data: { source: 'prometheus',   target: 'loki',          label: 'scrape' } },
      { data: { source: 'prometheus',   target: 'promtail',      label: 'scrape' } },
      { data: { source: 'prometheus',   target: 'grafana',       label: 'scrape' } },
      { data: { source: 'prometheus',   target: 'alertmanager',  label: 'alerts' } },
      { data: { source: 'promtail',     target: 'loki',          label: 'push logs' } },
      { data: { source: 'grafana',      target: 'prometheus',    label: 'query' } },
      { data: { source: 'grafana',      target: 'loki',          label: 'query' } },
      { data: { source: 'grafana',      target: 'alertmanager',  label: 'read alerts' } },
    ],
  },

  prometheus_targets: {
    nodes: [
      { data: { id: 'job-prometheus',    label: 'prometheus',    type: 'job', health: 'up' } },
      { data: { id: 'job-node',          label: 'node',          type: 'job', health: 'up' } },
      { data: { id: 'job-node-target1',  label: 'node-target1',  type: 'job', health: 'up' } },
      { data: { id: 'job-cadvisor',      label: 'cadvisor',      type: 'job', health: 'up' } },
      { data: { id: 'job-loki',          label: 'loki',          type: 'job', health: 'up' } },
      { data: { id: 'job-promtail',      label: 'promtail',      type: 'job', health: 'up' } },
      { data: { id: 'job-grafana',       label: 'grafana',       type: 'job', health: 'up' } },
      { data: { id: 'job-alertmanager',  label: 'alertmanager',  type: 'job', health: 'up' } },
      { data: { id: 'inst-prometheus',   label: 'saconsole:9090', type: 'instance', health: 'up', job: 'prometheus',   lastScrape: '1s ago' } },
      { data: { id: 'inst-node',         label: 'host.docker.internal:9100', type: 'instance', health: 'up', job: 'node',         lastScrape: '4s ago' } },
      { data: { id: 'inst-target1',      label: '10.10.1.3:9100', type: 'instance', health: 'up', job: 'node-target1', lastScrape: '2s ago' } },
      { data: { id: 'inst-cadvisor',     label: 'saconsole:8080', type: 'instance', health: 'up', job: 'cadvisor',     lastScrape: '3s ago' } },
      { data: { id: 'inst-loki',         label: 'saconsole:3100', type: 'instance', health: 'up', job: 'loki',         lastScrape: '5s ago' } },
      { data: { id: 'inst-promtail',     label: 'saconsole:9080', type: 'instance', health: 'up', job: 'promtail',     lastScrape: '1s ago' } },
      { data: { id: 'inst-grafana',      label: 'saconsole:3000', type: 'instance', health: 'up', job: 'grafana',      lastScrape: '2s ago' } },
      { data: { id: 'inst-alertmanager', label: 'saconsole:9093', type: 'instance', health: 'up', job: 'alertmanager', lastScrape: '4s ago' } },
    ],
    edges: [
      { data: { source: 'job-prometheus',   target: 'inst-prometheus',   label: '' } },
      { data: { source: 'job-node',         target: 'inst-node',         label: '' } },
      { data: { source: 'job-node-target1', target: 'inst-target1',      label: '' } },
      { data: { source: 'job-cadvisor',     target: 'inst-cadvisor',     label: '' } },
      { data: { source: 'job-loki',         target: 'inst-loki',         label: '' } },
      { data: { source: 'job-promtail',     target: 'inst-promtail',     label: '' } },
      { data: { source: 'job-grafana',      target: 'inst-grafana',      label: '' } },
      { data: { source: 'job-alertmanager', target: 'inst-alertmanager', label: '' } },
    ],
  },

}

// ── Data transformers ──────────────────────────────────────────────────────

function dockerContainersToGraph(containers) {
  // containers: array from Docker GET /containers/json
  const nodes = containers.map(c => ({
    data: {
      id:     c.Names?.[0]?.replace(/^\//, '') ?? c.Id.slice(0, 12),
      label:  c.Names?.[0]?.replace(/^\//, '') ?? c.Id.slice(0, 12),
      image:  c.Image,
      status: c.Status,
      state:  c.State,
      ports:  Object.values(c.Ports ?? {}).flat()
                .map(p => p.PublicPort ?? p.PrivatePort)
                .filter(Boolean).join(', ') || '—',
    }
  }))
  // No meaningful edges from a flat container list; will come from docker inspect / networks
  return { nodes, edges: [] }
}

function prometheusTargetsToGraph(data) {
  // data: body.data from GET /api/v1/targets
  const nodes = []
  const edges = []
  const jobSeen = {}

  for (const t of (data.activeTargets ?? [])) {
    const job      = t.labels.job ?? 'unknown'
    const instance = t.labels.instance ?? t.scrapeUrl
    const jobId    = `job-${job}`
    const instId   = `inst-${job}-${instance}`.replace(/[^\w-]/g, '_')

    if (!jobSeen[job]) {
      jobSeen[job] = true
      nodes.push({ data: { id: jobId, label: job, type: 'job', health: t.health } })
    }
    nodes.push({
      data: {
        id:         instId,
        label:      instance,
        type:       'instance',
        health:     t.health,
        job,
        lastScrape: t.lastScrape ? new Date(t.lastScrape).toLocaleTimeString() : '—',
        scrapeUrl:  t.scrapeUrl,
      }
    })
    edges.push({ data: { source: jobId, target: instId, label: '' } })
  }

  return { nodes, edges }
}

// ── Fetch functions ────────────────────────────────────────────────────────

async function fetchDockerContainers() {
  // Docker daemon does not expose HTTP by default.
  // This targets a future saconsole REST bridge at DOCKER_API.
  // Falls back to static data when unreachable.
  try {
    const res = await fetch(`${DOCKER_API}/docker/containers`, {
      signal: AbortSignal.timeout(3000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.info('[registry] Docker containers: live data (%d)', data.length)
    return dockerContainersToGraph(data)
  } catch (err) {
    console.warn('[registry] Docker API unreachable — using fallback:', err.message)
    return FALLBACK.saconsole_containers
  }
}

async function fetchPrometheusTargets() {
  // Prometheus exposes /api/v1/targets over HTTP.
  // Reachable from Xubuntu (Platform 2); CORS may block a browser on Windows.
  // Add a Vite proxy (server.proxy in vite.config.js) to work around CORS.
  try {
    const res = await fetch(`${PROMETHEUS}/api/v1/targets`, {
      signal: AbortSignal.timeout(3000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const { data } = await res.json()
    console.info('[registry] Prometheus targets: live data (%d active)', data.activeTargets?.length ?? 0)
    return prometheusTargetsToGraph(data)
  } catch (err) {
    console.warn('[registry] Prometheus API unreachable — using fallback:', err.message)
    return FALLBACK.prometheus_targets
  }
}

// ── ERPNext host inspection ────────────────────────────────────────────────
// Each ERPNext VM shows a 3-box service diagram (Web / App / DB).
// Status dots are fetched live from /api/health/{hostname} with amber fallback.

async function fetchErpnextServiceMap(hostname) {
  // Fetch live health; fall back to amber (unknown) on any failure
  let health = { web: 'unknown', app: 'unknown', db: 'unknown' }
  try {
    const res = await fetch(`/api/health/${hostname}`, {
      signal: AbortSignal.timeout(10000),
    })
    if (res.ok) health = await res.json()
  } catch {
    /* remain amber */
  }

  // Return a synthetic graph: 3 service nodes + connecting edges.
  // The popup renders them via a custom layout rather than Cytoscape's cose.
  return {
    nodes: [
      {
        data: {
          id:      'svc-web',
          label:   'Web',
          svcType: 'web',
          status:  health.web,
          detail1Key: 'Server',   detail1Val: 'Nginx',
          detail2Key: 'Protocol', detail2Val: 'HTTPS / TLS 1.2+',
          detail3Key: 'Redirect', detail3Val: 'HTTP → HTTPS',
        },
      },
      {
        data: {
          id:      'svc-app',
          label:   'Application',
          svcType: 'app',
          status:  health.app,
          detail1Key: 'Runtime',    detail1Val: 'ERPNext / Frappe',
          detail2Key: 'Supervisor', detail2Val: 'gunicorn + redis + socketio',
          detail3Key: 'User',       detail3Val: hostname, // will be overridden in popup
        },
      },
      {
        data: {
          id:      'svc-db',
          label:   'Database',
          svcType: 'db',
          status:  health.db,
          detail1Key: 'Engine',  detail1Val: 'MariaDB 10.11',
          detail2Key: 'Port',    detail2Val: '3306 (internal only)',
          detail3Key: 'Backups', detail3Val: 'BKP/ + BaRe/ scripts',
        },
      },
    ],
    edges: [
      { data: { source: 'svc-web', target: 'svc-app', label: 'proxy' } },
      { data: { source: 'svc-app', target: 'svc-db',  label: 'SQL' } },
    ],
  }
}

// Factory: creates a fetch function bound to a specific hostname
function erpnextFetcher(hostname) {
  return () => fetchErpnextServiceMap(hostname)
}

// ── Registry ───────────────────────────────────────────────────────────────
// Keyed by node ID in the parent graph.
// children keys must match IDs that fetch() will produce for that level.

export const registry = {
  saconsole: {
    label: 'saconsole',
    fetch: fetchDockerContainers,
    children: {
      prometheus: {
        label: 'prometheus',
        fetch: fetchPrometheusTargets,
        children: {},
      },
    },
  },

  // ERPNext dev VMs — 3-box service view; rendered by popup.js svcGrid mode
  dev01:   { label: 'dev01',   fetch: erpnextFetcher('dev01'),   mode: 'svc', children: {} },
  dev02:   { label: 'dev02',   fetch: erpnextFetcher('dev02'),   mode: 'svc', children: {} },
  target3: { label: 'target3', fetch: erpnextFetcher('target3'), mode: 'svc', children: {} },
}

// Resolve a path array to a registry entry.
// resolve(['saconsole', 'prometheus']) → registry.saconsole.children.prometheus
export function resolve(path) {
  let node = { children: registry }
  for (const key of path) {
    node = node.children?.[key]
    if (!node) return null
  }
  return node
}
