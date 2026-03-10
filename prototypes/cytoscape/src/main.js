import './style.css'
import cytoscape from 'cytoscape'
import { openPopup } from './popup.js'
import { registry } from './registry.js'

// ── Topology data ─────────────────────────────────────────────────────────────
// Mirrors hosts_map.yml. Swap static values for live API calls when ready.

const nodes = [
  {
    data: {
      id: 'controller',
      label: 'controller\n(WSL host)',
      role: 'controller',
      platform: 'wsl',
      wg_ip: '10.10.0.2',
    }
  },
  {
    data: {
      id: 'saconsole',
      label: 'saconsole\n[click to expand]',
      role: 'hub',
      platform: 'kvm',
      virbr0_ip: '192.168.122.10',
      wg_ip: '10.10.0.1',
      services: 'Prometheus · Grafana · Loki · Alertmanager',
    }
  },
  {
    data: {
      id: 'target1',
      label: 'target1',
      role: 'spoke',
      platform: 'kvm',
      virbr0_ip: '192.168.122.11',
      wg_ip: '10.10.0.3',
      services: 'node_exporter',
    }
  },
]

const edges = [
  {
    data: {
      id: 'ctrl-sac',
      source: 'controller',
      target: 'saconsole',
      label: 'WireGuard',
      type: 'wireguard',
    }
  },
  {
    data: {
      id: 'ctrl-tgt',
      source: 'controller',
      target: 'target1',
      label: 'WireGuard',
      type: 'wireguard',
    }
  },
  {
    data: {
      id: 'sac-tgt',
      source: 'saconsole',
      target: 'target1',
      label: 'WireGuard',
      type: 'wireguard',
    }
  },
]

// ── Main Cytoscape instance ───────────────────────────────────────────────────

const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: { nodes, edges },

  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#0f3460',
        'border-color': '#a0c4ff',
        'border-width': 1,
        'label': 'data(label)',
        'color': '#e0e0e0',
        'font-family': 'monospace',
        'font-size': '11px',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        'width': 80,
        'height': 80,
      }
    },
    {
      selector: 'node[role = "hub"]',
      style: {
        'background-color': '#1a4a7a',
        'border-color': '#4fc3f7',
        'border-width': 2,
        'border-style': 'double',
        'width': 100,
        'height': 100,
      }
    },
    {
      selector: 'node[role = "controller"]',
      style: {
        'background-color': '#2a2a0e',
        'border-color': '#c8e6a0',
        'border-style': 'dashed',
      }
    },
    {
      selector: 'node:selected',
      style: {
        'border-color': '#ffcc00',
        'border-width': 3,
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 1.5,
        'line-color': '#0f3460',
        'target-arrow-color': '#0f3460',
        'target-arrow-shape': 'none',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'color': '#555',
        'font-family': 'monospace',
        'font-size': '9px',
        'text-rotation': 'autorotate',
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#ffcc00',
        'color': '#ffcc00',
      }
    },
  ],

  layout: {
    name: 'breadthfirst',
    directed: false,
    padding: 40,
    spacingFactor: 1.8,
  },
})

// ── Info panel ────────────────────────────────────────────────────────────────

const infoPanel = document.getElementById('info-panel')

function renderInfo(data) {
  const rows = Object.entries(data)
    .filter(([k]) => k !== 'id')
    .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
    .join('')
  infoPanel.innerHTML = `<table>${rows}</table>`
}

cy.on('tap', 'node, edge', (evt) => {
  const data = evt.target.data()
  if (registry[data.id]) {
    openPopup(data.id)
  } else {
    renderInfo(data)
  }
})

cy.on('tap', (evt) => {
  if (evt.target === cy) {
    infoPanel.innerHTML = '<p class="hint">Click a node or edge to inspect it. Nodes with a registry entry open a drill-down view.</p>'
  }
})

// ── Resize handle ─────────────────────────────────────────────────────────────

const cyEl        = document.getElementById('cy')
const infoPanelEl = document.getElementById('info-panel')
const handle      = document.getElementById('resize-handle')
const header      = document.querySelector('header')

let resizing = false

handle.addEventListener('mousedown', (e) => {
  resizing = true
  handle.classList.add('dragging')
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'ns-resize'
  e.preventDefault()
})

document.addEventListener('mousemove', (e) => {
  if (!resizing) return

  const appTop    = header.getBoundingClientRect().bottom
  const appBottom = document.getElementById('app').getBoundingClientRect().bottom
  const handleH   = handle.offsetHeight

  const newCyH   = e.clientY - appTop
  const newInfoH = appBottom - e.clientY - handleH

  if (newCyH > 80 && newInfoH > 40) {
    cyEl.style.flex   = 'none'
    cyEl.style.height = newCyH + 'px'
    infoPanelEl.style.height = newInfoH + 'px'
    cy.resize()
  }
})

document.addEventListener('mouseup', () => {
  if (!resizing) return
  resizing = false
  handle.classList.remove('dragging')
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
})
