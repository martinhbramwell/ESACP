// containers.js — Docker container topology for the saconsole popup
// Data mirrors docker/observability/docker-compose.yml.
// Replace static data with live Docker API / Prometheus calls when ready.

import cytoscape from 'cytoscape'

// ── Container data ─────────────────────────────────────────────────────────

const elements = {
  nodes: [
    {
      data: {
        id: 'grafana',
        label: 'grafana',
        vendor: 'grafana',
        image: 'grafana/grafana:10.2.3',
        port: '3000',
        status: 'running',
      }
    },
    {
      data: {
        id: 'prometheus',
        label: 'prometheus',
        vendor: 'prometheus',
        image: 'prom/prometheus:v2.48.1',
        port: '9090',
        status: 'running',
      }
    },
    {
      data: {
        id: 'alertmanager',
        label: 'alertmanager',
        vendor: 'prometheus',
        image: 'prom/alertmanager:v0.26.0',
        port: '9093',
        status: 'running',
      }
    },
    {
      data: {
        id: 'node_exporter',
        label: 'node_exporter',
        vendor: 'prometheus',
        image: 'prom/node-exporter:v1.7.0',
        port: '9100',
        network: 'host',
        status: 'running',
      }
    },
    {
      data: {
        id: 'cadvisor',
        label: 'cadvisor',
        vendor: 'prometheus',
        image: 'gcr.io/cadvisor/cadvisor:v0.55.1',
        port: '8080',
        status: 'running',
      }
    },
    {
      data: {
        id: 'loki',
        label: 'loki',
        vendor: 'grafana',
        image: 'grafana/loki:2.9.3',
        port: '3100',
        status: 'running',
      }
    },
    {
      data: {
        id: 'promtail',
        label: 'promtail',
        vendor: 'grafana',
        image: 'grafana/promtail:3.3.2',
        port: '9080 (internal)',
        status: 'running',
      }
    },
  ],

  edges: [
    // Prometheus scrapes
    { data: { source: 'prometheus', target: 'node_exporter', label: 'scrape' } },
    { data: { source: 'prometheus', target: 'cadvisor',      label: 'scrape' } },
    { data: { source: 'prometheus', target: 'loki',          label: 'scrape' } },
    { data: { source: 'prometheus', target: 'promtail',      label: 'scrape' } },
    { data: { source: 'prometheus', target: 'grafana',       label: 'scrape' } },
    // Alert pipeline
    { data: { source: 'prometheus',    target: 'alertmanager', label: 'fire alerts' } },
    { data: { source: 'prometheus',    target: 'alertmanager', label: 'scrape' } },
    // Log pipeline
    { data: { source: 'promtail', target: 'loki', label: 'push logs' } },
    // Grafana queries
    { data: { source: 'grafana', target: 'prometheus',    label: 'query' } },
    { data: { source: 'grafana', target: 'loki',          label: 'query' } },
    { data: { source: 'grafana', target: 'alertmanager',  label: 'read alerts' } },
  ],
}

// ── Popup lifecycle ────────────────────────────────────────────────────────

let popupCy = null

const overlay   = document.getElementById('popup-overlay')
const closeBtn  = document.getElementById('popup-close')
const popupInfo = document.getElementById('popup-info')

function renderPopupInfo(data) {
  const rows = Object.entries(data)
    .filter(([k]) => k !== 'id')
    .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
    .join('')
  popupInfo.innerHTML = `<table>${rows}</table>`
}

function initPopupCy() {
  popupCy = cytoscape({
    container: document.getElementById('popup-cy'),
    elements,

    style: [
      {
        selector: 'node',
        style: {
          'shape': 'rectangle',
          'background-color': '#0d2137',
          'border-width': 1.5,
          'border-color': '#2a5a9a',
          'label': 'data(label)',
          'color': '#e0e0e0',
          'font-family': 'monospace',
          'font-size': '10px',
          'text-valign': 'center',
          'text-halign': 'center',
          'width': 90,
          'height': 36,
        }
      },
      {
        // Grafana-vendor containers: orange border
        selector: 'node[vendor = "grafana"]',
        style: {
          'border-color': '#F46800',
          'background-color': '#2a1400',
        }
      },
      {
        // Prometheus-vendor containers: red-orange border
        selector: 'node[vendor = "prometheus"]',
        style: {
          'border-color': '#E6522C',
          'background-color': '#2a0f08',
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-color': '#ffcc00',
          'border-width': 2.5,
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 1,
          'line-color': '#1a3a5c',
          'target-arrow-color': '#1a3a5c',
          'target-arrow-shape': 'triangle',
          'arrow-scale': 0.8,
          'curve-style': 'bezier',
          'label': 'data(label)',
          'color': '#445',
          'font-family': 'monospace',
          'font-size': '8px',
          'text-rotation': 'autorotate',
          'text-background-color': '#1a1a2e',
          'text-background-opacity': 1,
          'text-background-padding': '2px',
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'line-color': '#ffcc00',
          'target-arrow-color': '#ffcc00',
          'color': '#ffcc00',
        }
      },
    ],

    layout: {
      name: 'cose',
      animate: false,
      padding: 30,
      nodeRepulsion: 12000,
      idealEdgeLength: 80,
      gravity: 0.6,
    },
  })

  popupCy.on('tap', 'node, edge', (evt) => {
    renderPopupInfo(evt.target.data())
  })

  popupCy.on('tap', (evt) => {
    if (evt.target === popupCy) {
      popupInfo.innerHTML = '<p class="hint">Click a container to inspect it.</p>'
    }
  })
}

export function showContainerPopup() {
  overlay.classList.remove('hidden')
  // Defer init/resize until the container has layout dimensions
  requestAnimationFrame(() => {
    if (!popupCy) {
      initPopupCy()
    } else {
      popupCy.resize()
      popupCy.fit(undefined, 30)
    }
    popupInfo.innerHTML = '<p class="hint">Click a container to inspect it.</p>'
  })
}

function hidePopup() {
  overlay.classList.add('hidden')
}

closeBtn.addEventListener('click', hidePopup)

// Click outside the popup panel to close
overlay.addEventListener('click', (evt) => {
  if (evt.target === overlay) hidePopup()
})

// Escape key to close
document.addEventListener('keydown', (evt) => {
  if (evt.key === 'Escape') hidePopup()
})
