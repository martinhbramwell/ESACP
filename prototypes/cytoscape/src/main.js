import './style.css'
import cytoscape from 'cytoscape'
import { openPopup } from './popup.js'
import { registry } from './registry.js'
import { fetchHosts, addHost, startProvision, pollJob } from './api.js'

// ── Fallback topology (used when API is unreachable) ─────────────────────────
// Mirrors the current Stage 2.2 estate on toshiba.

const FALLBACK_HOSTS = [
  { id: 'saconsole', hostname: 'saconsole', wg_role: 'hub',   wg_ip: '10.10.0.1', virbr0_ip: '192.168.122.10', backend: 'kvm', provisioned: true },
  { id: 'target1',   hostname: 'target1',   wg_role: 'spoke', wg_ip: '10.10.0.3', virbr0_ip: '192.168.122.11', backend: 'kvm', provisioned: true },
  { id: 'target2',   hostname: 'target2',   wg_role: 'spoke', wg_ip: '10.10.0.4', virbr0_ip: '192.168.122.12', backend: 'kvm', provisioned: true },
]

// The controller is always "this machine" — not fetched from API
const CONTROLLER_NODE = {
  data: {
    id:          'controller',
    label:       'controller\n(Mighty)',
    role:        'controller',
    platform:    'xubuntu',
    wg_ip:       '10.10.0.2',
    provisioned: true,
  }
}

// ── Graph data builder ────────────────────────────────────────────────────────

function buildNodesEdges(apiHosts) {
  const hosts = apiHosts ?? FALLBACK_HOSTS
  const hub   = hosts.find(h => h.wg_role === 'hub')

  const nodes = [
    CONTROLLER_NODE,
    ...hosts.map(h => ({
      data: {
        id:          h.hostname,
        label:       h.provisioned === false
                       ? `${h.hostname}\n[unprovisioned]`
                       : h.hostname,
        role:        h.wg_role === 'hub' ? 'hub' : 'spoke',
        platform:    h.backend ?? 'kvm',
        wg_ip:       h.wg_ip    ?? '',
        virbr0_ip:   h.virbr0_ip ?? '',
        provisioned: h.provisioned !== false,
      }
    })),
  ]

  const edges = []

  // Controller → hub
  if (hub) {
    edges.push({
      data: { id: 'ctrl-hub', source: 'controller', target: hub.hostname, label: 'WireGuard', type: 'wireguard' }
    })
  }

  // Every non-hub spoke ↔ hub (and controller → spoke for reachability edges)
  hosts.filter(h => h.wg_role !== 'hub').forEach(h => {
    if (hub) {
      edges.push({
        data: { id: `wg-${h.hostname}`, source: hub.hostname, target: h.hostname, label: 'WireGuard', type: 'wireguard' }
      })
    }
  })

  return { nodes, edges }
}

// ── Cytoscape styles ──────────────────────────────────────────────────────────

const CY_STYLE = [
  {
    selector: 'node',
    style: {
      'background-color': '#0f3460',
      'border-color':     '#a0c4ff',
      'border-width':     1,
      'label':            'data(label)',
      'color':            '#e0e0e0',
      'font-family':      'monospace',
      'font-size':        '11px',
      'text-valign':      'center',
      'text-halign':      'center',
      'text-wrap':        'wrap',
      'width':            80,
      'height':           80,
    }
  },
  {
    selector: 'node[role = "hub"]',
    style: {
      'background-color': '#1a4a7a',
      'border-color':     '#4fc3f7',
      'border-width':     2,
      'border-style':     'double',
      'width':            100,
      'height':           100,
    }
  },
  {
    selector: 'node[role = "controller"]',
    style: {
      'background-color': '#2a2a0e',
      'border-color':     '#c8e6a0',
      'border-style':     'dashed',
    }
  },
  {
    // Unprovisioned (newly drawn) targets — dashed amber border
    // [!provisioned] matches falsy: false, 0, '', null, undefined
    selector: 'node[!provisioned]',
    style: {
      'background-color': '#1a1a0a',
      'border-color':     '#f0a020',
      'border-width':     2,
      'border-style':     'dashed',
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
      'width':              1.5,
      'line-color':         '#0f3460',
      'target-arrow-color': '#0f3460',
      'target-arrow-shape': 'none',
      'curve-style':        'bezier',
      'label':              'data(label)',
      'color':              '#555',
      'font-family':        'monospace',
      'font-size':          '9px',
      'text-rotation':      'autorotate',
    }
  },
  {
    selector: 'edge:selected',
    style: { 'line-color': '#ffcc00', 'color': '#ffcc00' }
  },
]

// ── Initialise graph ──────────────────────────────────────────────────────────

let cy = null
let apiSuggestions = { wg_ip: '10.10.0.5', virbr0_ip: '192.168.122.13' }

const apiStatusEl = document.getElementById('api-status')

function setApiStatus(ok) {
  apiStatusEl.className = `api-status api-status--${ok ? 'ok' : 'error'}`
  apiStatusEl.title     = ok ? 'API connected (localhost:8088)' : 'API unreachable — using fallback data'
}

async function init() {
  let hosts = null

  try {
    const data    = await fetchHosts()
    hosts         = data.hosts
    apiSuggestions = data.suggestions
    setApiStatus(true)
  } catch {
    setApiStatus(false)
  }

  const { nodes, edges } = buildNodesEdges(hosts)

  cy = cytoscape({
    container: document.getElementById('cy'),
    elements:  { nodes, edges },
    style:     CY_STYLE,
    layout: {
      name:          'breadthfirst',
      directed:      false,
      padding:       40,
      spacingFactor: 1.8,
    },
  })

  attachHandlers()
}

// ── Info panel ────────────────────────────────────────────────────────────────

const infoPanel = document.getElementById('info-panel')

function hint(msg) {
  infoPanel.innerHTML = `<p class="hint">${msg}</p>`
}

function renderInfo(data) {
  const skip = new Set(['id'])
  const rows = Object.entries(data)
    .filter(([k]) => !skip.has(k))
    .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
    .join('')
  infoPanel.innerHTML = `<table>${rows}</table>`
}

function renderInfoWithProvision(data) {
  renderInfo(data)
  const btn = document.createElement('button')
  btn.className   = 'provision-btn'
  btn.textContent = 'Provision'
  btn.onclick     = () => runProvision(data.id)
  infoPanel.appendChild(btn)
}

function renderJobLog(lines, done, status) {
  let pre = infoPanel.querySelector('pre.job-log')
  if (!pre) {
    infoPanel.innerHTML = ''
    pre = document.createElement('pre')
    pre.className = 'job-log'
    infoPanel.appendChild(pre)
  }
  pre.textContent += lines.join('\n') + (lines.length ? '\n' : '')
  pre.scrollTop = pre.scrollHeight

  if (done) {
    const badge     = document.createElement('span')
    badge.className = `job-badge job-badge--${status}`
    badge.textContent = status === 'done' ? ' Done' : ' Failed'
    infoPanel.appendChild(badge)
  }
}

// ── Provision flow ────────────────────────────────────────────────────────────

function runProvision(hostname) {
  infoPanel.innerHTML = `<pre class="job-log">Starting provisioning for ${hostname}...\n</pre>`

  startProvision(hostname)
    .then(({ job_id }) => {
      pollJob(
        job_id,
        lines  => renderJobLog(lines, false, null),
        status => {
          renderJobLog([], true, status)
          // Update node styling on success
          if (status === 'done') {
            const node = cy.$(`#${hostname}`)
            node.data('provisioned', true)
            node.data('label', hostname)
          }
        }
      )
    })
    .catch(err => {
      infoPanel.innerHTML = `<p class="hint error">Provision failed: ${err.message}</p>`
    })
}

// ── Event handlers ────────────────────────────────────────────────────────────

function attachHandlers() {
  // Node / edge tap — info panel or drill-down
  cy.on('tap', 'node, edge', evt => {
    const data = evt.target.data()

    if (data.provisioned === false) {
      renderInfoWithProvision(data)
      return
    }

    if (registry[data.id]) {
      openPopup(data.id)
    } else {
      renderInfo(data)
    }
  })

  // Canvas tap — clear info
  cy.on('tap', evt => {
    if (evt.target === cy) {
      hint('Click a node or edge to inspect it. Right-click the canvas to add a target.')
    }
  })

  // Right-click on canvas background — show context menu
  cy.on('cxttap', evt => {
    if (evt.target !== cy) return
    const { x, y } = evt.originalEvent
    showCtxMenu(x, y)
  })
}

// ── Context menu ──────────────────────────────────────────────────────────────

const ctxMenu = document.getElementById('ctx-menu')

function showCtxMenu(x, y) {
  ctxMenu.style.left = `${x}px`
  ctxMenu.style.top  = `${y}px`
  ctxMenu.classList.remove('hidden')
}

function hideCtxMenu() {
  ctxMenu.classList.add('hidden')
}

document.getElementById('ctx-add-target').addEventListener('click', () => {
  hideCtxMenu()
  openDialog()
})

document.addEventListener('click', e => {
  if (!ctxMenu.contains(e.target)) hideCtxMenu()
})

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') hideCtxMenu()
})

// ── Add Target dialog ─────────────────────────────────────────────────────────

const dialogOverlay = document.getElementById('dialog-overlay')
const dialogError   = document.getElementById('dialog-error')
const fHostname     = document.getElementById('f-hostname')
const fNickname     = document.getElementById('f-nickname')
const fWgIp         = document.getElementById('f-wg-ip')
const fVirbr0Ip     = document.getElementById('f-virbr0-ip')
const fBackend      = document.getElementById('f-backend')
const submitBtn     = document.getElementById('dialog-submit')

function openDialog() {
  fHostname.value  = ''
  fNickname.value  = ''
  fWgIp.value      = apiSuggestions.wg_ip
  fVirbr0Ip.value  = apiSuggestions.virbr0_ip
  fBackend.value   = 'kvm'
  dialogError.classList.add('hidden')
  dialogError.textContent = ''
  submitBtn.disabled = false
  dialogOverlay.classList.remove('hidden')
  fHostname.focus()
}

function closeDialog() {
  dialogOverlay.classList.add('hidden')
}

document.getElementById('dialog-cancel').addEventListener('click', closeDialog)

dialogOverlay.addEventListener('click', e => {
  if (e.target === dialogOverlay) closeDialog()
})

document.getElementById('add-target-form').addEventListener('submit', async e => {
  e.preventDefault()
  dialogError.classList.add('hidden')
  submitBtn.disabled = true
  submitBtn.textContent = 'Adding…'

  const hostname  = fHostname.value.trim()
  const nickname  = fNickname.value.trim()
  const wg_ip     = fWgIp.value.trim()
  const virbr0_ip = fVirbr0Ip.value.trim()
  const backend   = fBackend.value

  try {
    await addHost({ hostname, nickname, virbr0_ip, wg_ip, backend })
    closeDialog()
    _addNodeToGraph({ hostname, nickname, virbr0_ip, wg_ip, backend })
    // Refresh suggestions for the next add
    fetchHosts()
      .then(d => { apiSuggestions = d.suggestions })
      .catch(() => {})
  } catch (err) {
    dialogError.textContent = err.message
    dialogError.classList.remove('hidden')
    submitBtn.disabled   = false
    submitBtn.textContent = 'Add'
  }
})

function _addNodeToGraph({ hostname, wg_ip, virbr0_ip, backend }) {
  // Add node with unprovisioned styling
  cy.add({
    group: 'nodes',
    data: {
      id:          hostname,
      label:       `${hostname}\n[unprovisioned]`,
      role:        'spoke',
      platform:    backend,
      wg_ip,
      virbr0_ip,
      provisioned: false,
    },
  })

  // Connect to hub
  const hub = cy.nodes('[role = "hub"]').first()
  if (hub.length) {
    cy.add({
      group: 'edges',
      data: {
        id:     `wg-${hostname}`,
        source: hub.id(),
        target: hostname,
        label:  'WireGuard',
        type:   'wireguard',
      },
    })
  }

  // Re-run layout to place the new node
  cy.layout({
    name:          'breadthfirst',
    directed:      false,
    padding:       40,
    spacingFactor: 1.8,
    fit:           false,
  }).run()
}

// ── Resize handle ─────────────────────────────────────────────────────────────

const cyEl        = document.getElementById('cy')
const infoPanelEl = document.getElementById('info-panel')
const handle      = document.getElementById('resize-handle')
const header      = document.querySelector('header')

let resizing = false

handle.addEventListener('mousedown', e => {
  resizing = true
  handle.classList.add('dragging')
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'ns-resize'
  e.preventDefault()
})

document.addEventListener('mousemove', e => {
  if (!resizing) return
  const appTop    = header.getBoundingClientRect().bottom
  const appBottom = document.getElementById('app').getBoundingClientRect().bottom
  const handleH   = handle.offsetHeight
  const newCyH    = e.clientY - appTop
  const newInfoH  = appBottom - e.clientY - handleH
  if (newCyH > 80 && newInfoH > 40) {
    cyEl.style.flex       = 'none'
    cyEl.style.height     = newCyH + 'px'
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

// ── Boot ──────────────────────────────────────────────────────────────────────

init()
