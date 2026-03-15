// registry.js — recursive drill-down data registry
//
// Each entry: { label, fetch: async () => { nodes, edges }, children: { ... } }
// fetch() returns the graph data for that level.
// children keys must match node IDs returned by the parent's fetch().
//
// All live data flows through the ESACP API (port 8088) on saconsole.
// This avoids CORS issues: the API returns Access-Control-Allow-Origin: *
// and proxies Prometheus internally over observability_network.
//
// Platform configuration: set VITE_SACONSOLE in prototypes/cytoscape/.env.local
//   KVM/Xubuntu:  VITE_SACONSOLE=http://192.168.122.10   (default)
//   VBox/WSL:     VITE_SACONSOLE=http://192.168.40.50

const SACONSOLE  = import.meta.env.VITE_SACONSOLE ?? 'http://192.168.122.10'
const DOCKER_API = `${SACONSOLE}:8088`

// ── Fallback static data ───────────────────────────────────────────────────
// Realistic snapshots used when the live API is unreachable.

const FALLBACK = {

  saconsole_containers: {
    nodes: [
      { data: { id: 'grafana',       label: 'grafana',       image: 'grafana/grafana:10.2.3',            status: 'running', state: 'running', ports: '3000' } },
      { data: { id: 'prometheus',    label: 'prometheus',    image: 'prom/prometheus:v2.48.1',           status: 'running', state: 'running', ports: '9090' } },
      { data: { id: 'alertmanager',  label: 'alertmanager',  image: 'prom/alertmanager:v0.26.0',         status: 'running', state: 'running', ports: '9093' } },
      { data: { id: 'loki',          label: 'loki',          image: 'grafana/loki:2.9.3',               status: 'running', state: 'running', ports: '3100' } },
      { data: { id: 'promtail',      label: 'promtail',      image: 'grafana/promtail:3.3.2',           status: 'running', state: 'running', ports: '9080' } },
      { data: { id: 'node_exporter', label: 'node_exporter', image: 'prom/node-exporter:v1.7.0',        status: 'running', state: 'running', ports: '9100', network: 'host' } },
      { data: { id: 'cadvisor',      label: 'cadvisor',      image: 'gcr.io/cadvisor/cadvisor:v0.55.1', status: 'running', state: 'running', ports: '8080' } },
      { data: { id: 'esacp-api',     label: 'esacp-api',     image: 'esacp-api',                        status: 'running', state: 'running', ports: '8088' } },
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
  // containers: array from ESACP API GET /docker/containers
  // { id, name, image, status, state, ports: string[] }
  //
  // Edges: the flat container list has no relationship data.
  // Network topology comes from GET /docker/networks (future drill-down level).
  const nodes = containers.map(c => ({
    data: {
      id:     c.id,
      label:  c.name,
      image:  c.image,
      status: c.status,
      state:  c.state,
      ports:  Array.isArray(c.ports) ? (c.ports.join(', ') || '—') : (c.ports || '—'),
    }
  }))
  return { nodes, edges: [] }
}

function prometheusTargetsToGraph(data) {
  // data: body.data from GET /api/v1/targets (passed through from API proxy)
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
  try {
    const res = await fetch(`${DOCKER_API}/docker/containers`, {
      signal: AbortSignal.timeout(3000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    console.info('[registry] Docker containers: live data (%d)', data.length)
    return dockerContainersToGraph(data)
  } catch (err) {
    console.warn('[registry] ESACP API unreachable — using fallback:', err.message)
    return FALLBACK.saconsole_containers
  }
}

async function fetchPrometheusTargets() {
  // Routes through the ESACP API proxy (/prometheus/targets) so the browser
  // does not need direct access to Prometheus and CORS is not an issue.
  try {
    const res = await fetch(`${DOCKER_API}/prometheus/targets`, {
      signal: AbortSignal.timeout(3000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const { data } = await res.json()
    console.info('[registry] Prometheus targets: live data (%d active)', data.activeTargets?.length ?? 0)
    return prometheusTargetsToGraph(data)
  } catch (err) {
    console.warn('[registry] Prometheus proxy unreachable — using fallback:', err.message)
    return FALLBACK.prometheus_targets
  }
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
