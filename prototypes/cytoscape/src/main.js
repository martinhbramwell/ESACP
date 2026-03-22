import './style.css'
import cytoscape from 'cytoscape'
import { openPopup } from './popup.js'
import { registry } from './registry.js'
import { fetchHosts, fetchJobs, addHost, startProvision, startDestroy, pollJob } from './api.js'

// ── Zone definitions ──────────────────────────────────────────────────────────
// Four quadrants: Console (top-left, narrow), Dev (top-right),
// Staging (bottom-left), Production (bottom-right).
// Child node positions are in absolute graph coordinates.
// Compound parent nodes auto-size to their children.

const ZONE_DEFS = [
  { id: 'zone-console',    label: 'Console',     style: 'zone-console'    },
  { id: 'zone-dev',        label: 'Development', style: 'zone-dev'        },
  { id: 'zone-staging',    label: 'Staging',     style: 'zone-staging'    },
  { id: 'zone-production', label: 'Production',  style: 'zone-production' },
]

// Initial positions for known nodes (absolute graph coordinates).
// Dev targets spread rightward from x=500; each new target gets +150 x offset.
const INITIAL_POSITIONS = {
  controller: { x: 130, y: 200 },
  saconsole:  { x: 130, y: 380 },
  target1:    { x: 500, y: 150 },
  target2:    { x: 660, y: 150 },
  tgt3:       { x: 500, y: 310 },
  target4:    { x: 660, y: 310 },
}

function zoneFor(host) {
  if (host.wg_role === 'hub')    return 'zone-console'
  const g = host.ansible_groups ?? []
  if (g.includes('production')) return 'zone-production'
  if (g.includes('staging'))    return 'zone-staging'
  return 'zone-dev'   // spoke + development (default)
}

// Calculate a position for a newly added node in zone-dev
function nextDevPosition(cy) {
  const devNodes = cy.nodes('[zone_id = "zone-dev"]')
  const xs = devNodes.map(n => n.position('x'))
  const maxX = xs.length ? Math.max(...xs) : 440
  return { x: maxX + 160, y: 150 }
}

// ── Fallback topology ────────────────────────────────────────────────────────
const FALLBACK_HOSTS = [
  { id: 'saconsole', hostname: 'saconsole', wg_role: 'hub',   wg_ip: '10.10.0.1', virbr0_ip: '192.168.122.10', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'development', 'lab'] },
  { id: 'target1',   hostname: 'target1',   wg_role: 'spoke', wg_ip: '10.10.0.3', virbr0_ip: '192.168.122.11', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'targets', 'development', 'lab'] },
  { id: 'target2',   hostname: 'target2',   wg_role: 'spoke', wg_ip: '10.10.0.4', virbr0_ip: '192.168.122.12', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'targets', 'development', 'lab'] },
]

const CONTROLLER_HOST = {
  id: 'controller', hostname: 'controller', wg_role: 'controller',
  wg_ip: '10.10.0.2', virbr0_ip: '', backend: 'local',
  provisioned: true, ansible_groups: [],
}

// ── Graph data builder ────────────────────────────────────────────────────────

function buildNodesEdges(apiHosts) {
  const hosts = apiHosts ?? FALLBACK_HOSTS
  const hub   = hosts.find(h => h.wg_role === 'hub')
  const allHosts = [CONTROLLER_HOST, ...hosts]

  // Zone parent nodes
  const zoneNodes = ZONE_DEFS.map(z => ({
    data: { id: z.id, label: z.label, zone: true },
  }))

  // VM / controller nodes — assigned to a zone parent
  const vmNodes = allHosts.map(h => {
    const zone = h.wg_role === 'controller' ? 'zone-console' : zoneFor(h)
    return {
      data: {
        id:            h.id ?? h.hostname,
        label:         h.provisioned === false ? `${h.hostname}\n[unprovisioned]`
                     : h.provisioned === null  ? `${h.hostname}\n[unknown]`
                     : h.hostname,
        role:          h.wg_role,
        platform:      h.backend ?? 'kvm',
        wg_ip:         h.wg_ip    ?? '',
        virbr0_ip:     h.virbr0_ip ?? '',
        provisioned:   !!h.provisioned,
        ansible_groups: h.ansible_groups ?? [],
        zone_id:       zone,
        parent:        zone,
      },
      position: INITIAL_POSITIONS[h.id ?? h.hostname],
    }
  })

  const edges = []
  if (hub) {
    edges.push({
      data: { id: 'ctrl-hub', source: 'controller', target: hub.hostname, label: 'WireGuard', type: 'wireguard' }
    })
    hosts.filter(h => h.wg_role !== 'hub').forEach(h => {
      edges.push({
        data: { id: `wg-${h.hostname}`, source: hub.hostname, target: h.hostname, label: 'WireGuard', type: 'wireguard' }
      })
    })
  }

  return { nodes: [...zoneNodes, ...vmNodes], edges }
}

// ── Cytoscape styles ──────────────────────────────────────────────────────────

const CY_STYLE = [
  // ── Zone compound nodes ──
  {
    selector: 'node[zone]',
    style: {
      'shape':              'rectangle',
      'background-color':   '#0a0a1a',
      'background-opacity': 0.5,
      'border-width':       2,
      'label':              'data(label)',
      'text-valign':        'top',
      'text-halign':        'left',
      'text-margin-x':      8,
      'text-margin-y':      4,
      'font-family':        'monospace',
      'font-size':          '13px',
      'font-weight':        'bold',
      'padding':            '35px',
      'events':             'no',    // zone backgrounds are not interactive
    }
  },
  { selector: '#zone-console',    style: { 'border-color': '#888888', 'color': '#aaaaaa' } },
  { selector: '#zone-dev',        style: { 'border-color': '#44aa66', 'color': '#44aa66' } },
  { selector: '#zone-staging',    style: { 'border-color': '#cc8833', 'color': '#cc8833' } },
  { selector: '#zone-production', style: { 'border-color': '#cc4444', 'color': '#cc4444' } },

  // ── VM nodes ──
  {
    selector: 'node:not([zone])',
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
    selector: 'node[!provisioned]',
    style: {
      'background-color': '#1a1a0a',
      'border-color':     '#f0a020',
      'border-width':     2,
      'border-style':     'dashed',
    }
  },
  {
    selector: 'node:selected:not([zone])',
    style: { 'border-color': '#ffcc00', 'border-width': 3 }
  },

  // ── Edges ──
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
  { selector: 'edge:selected', style: { 'line-color': '#ffcc00', 'color': '#ffcc00' } },
]

// ── Initialise graph ──────────────────────────────────────────────────────────

let cy = null
let apiSuggestions = { wg_ip: '10.10.0.7', virbr0_ip: '192.168.122.15', hypervisor: 'toshiba' }

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
      name:      'preset',
      animate:   false,
      // Nodes without a position in INITIAL_POSITIONS get placed at (0,0) inside their zone
      positions: node => INITIAL_POSITIONS[node.id()] || undefined,
    },
  })

  // Fit viewport to show all content with padding
  cy.fit(cy.elements(), 60)

  attachHandlers()
  _reconnectActiveJob()
}

// ── Info panel ────────────────────────────────────────────────────────────────

const infoPanel = document.getElementById('info-panel')

function hint(msg) {
  infoPanel.innerHTML = `<p class="hint">${msg}</p>`
}

function renderInfo(data) {
  const skip = new Set(['id', 'zone', 'ansible_groups', 'zone_id'])
  const rows = Object.entries(data)
    .filter(([k]) => !skip.has(k))
    .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
    .join('')
  infoPanel.innerHTML = `<table>${rows}</table>`
}

// Render info panel with all contextual action buttons for this node.
// Actions adapt to node state — no right-click required.
// No-op while a job is running: the job log must not be overwritten mid-flight.
function renderInfoWithActions(data) {
  if (activeJob) return
  renderInfo(data)

  const role        = data.role
  const provisioned = data.provisioned
  const isOperational = role !== 'controller' && role !== 'hub'

  const actions = document.createElement('div')
  actions.className = 'action-bar'

  if (isOperational && !provisioned) {
    const btn = document.createElement('button')
    btn.className   = 'action-btn'
    btn.textContent = 'Provision'
    btn.onclick     = () => runProvision(data.id)
    actions.appendChild(btn)
  }

  if (isOperational) {
    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--danger'
    btn.textContent = provisioned ? 'Destroy VM' : 'Remove'
    btn.onclick     = () => runDestroy(data.id, provisioned)
    actions.appendChild(btn)
  }

  if (registry[data.id] && provisioned) {
    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--inspect'
    btn.textContent = 'Inspect ›'
    btn.onclick     = () => openPopup(data.id)
    actions.appendChild(btn)
  }

  if (actions.childElementCount) infoPanel.appendChild(actions)
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

const JOB_KEY  = 'esacp_active_job'
let   activeJob = null  // { job_id, hostname, type } — set while a job is running

function runProvision(hostname) {
  infoPanel.innerHTML = `<pre class="job-log">Starting provisioning for ${hostname}...\n</pre>`

  startProvision(hostname)
    .then(({ job_id }) => {
      localStorage.setItem(JOB_KEY, JSON.stringify({ job_id, hostname, type: 'provision' }))
      _attachJobPoller(job_id, hostname, 'provision')
    })
    .catch(err => {
      infoPanel.innerHTML = `<p class="hint error">Provision failed: ${err.message}</p>`
    })
}

// ── Destroy flow ──────────────────────────────────────────────────────────────

// Opens the inline confirm modal — no browser dialog.
function runDestroy(hostname, provisioned = true) {
  showConfirmModal(hostname, provisioned)
}

// Called only when user clicks "Confirm Destroy" in the modal.
function _executeDestroy(hostname) {
  infoPanel.innerHTML = `<pre class="job-log">Starting destroy for ${hostname}...\n</pre>`

  startDestroy(hostname)
    .then(({ job_id }) => {
      localStorage.setItem(JOB_KEY, JSON.stringify({ job_id, hostname, type: 'destroy' }))
      _attachJobPoller(job_id, hostname, 'destroy')
    })
    .catch(err => {
      activeJob = null
      infoPanel.innerHTML = `<p class="hint error">Destroy failed: ${err.message}</p>`
    })
}

function _attachJobPoller(job_id, hostname, type) {
  activeJob = { job_id, hostname, type }
  pollJob(
    job_id,
    lines  => renderJobLog(lines, false, null),
    status => {
      renderJobLog([], true, status)
      activeJob = null
      localStorage.removeItem(JOB_KEY)
      if (status === 'done') {
        if (type === 'provision') {
          const node = cy.$(`#${hostname}`)
          node.data('provisioned', true)
          node.data('label', hostname)
        } else if (type === 'destroy') {
          // Remove node and all connected edges from the graph
          const node = cy.$(`#${hostname}`)
          cy.remove(node.connectedEdges())
          cy.remove(node)
          hint('Node destroyed. Use + Add Target to register a new VM.')
        }
      }
    }
  )
}

async function _reconnectActiveJob() {
  const stored = localStorage.getItem(JOB_KEY)
  if (!stored) return
  try {
    const { job_id, hostname, type } = JSON.parse(stored)
    const allJobs = await fetchJobs()
    const job = allJobs[job_id]
    if (!job || job.status !== 'running') { localStorage.removeItem(JOB_KEY); return }
    infoPanel.innerHTML = `<pre class="job-log">Reconnected to in-progress ${type ?? 'job'} for ${hostname}...\n</pre>`
    _attachJobPoller(job_id, hostname, type ?? 'provision')
  } catch {
    localStorage.removeItem(JOB_KEY)
  }
}

// ── Event handlers ────────────────────────────────────────────────────────────

function attachHandlers() {
  // Tap any VM node → info panel with contextual actions.
  // No right-click required — all actions are in the panel.
  cy.on('tap', 'node:not([zone])', evt => {
    renderInfoWithActions(evt.target.data())
  })

  // Tap edge → info only (guarded — don't overwrite job log)
  cy.on('tap', 'edge', evt => {
    if (activeJob) return
    renderInfo(evt.target.data())
  })

  // Tap canvas — clear info (guarded — don't overwrite job log)
  cy.on('tap', evt => {
    if (evt.target === cy) {
      if (activeJob) return
      hint('Click a node to inspect it or use + Add Target in the toolbar.')
    }
  })

  // Canvas right-click — power-user shortcut for Add Target
  cy.on('cxttap', evt => {
    if (evt.target === cy || evt.target.data('zone')) {
      const { x, y } = evt.originalEvent
      showCtxMenu(x, y)
    }
  })
}

// ── Canvas context menu ────────────────────────────────────────────────────────

const ctxMenu = document.getElementById('ctx-menu')

function showCtxMenu(x, y) {
  ctxMenu.style.left = `${x}px`
  ctxMenu.style.top  = `${y}px`
  ctxMenu.classList.remove('hidden')
}

function hideCtxMenu() {
  ctxMenu.classList.add('hidden')
}

// Header toolbar button — primary entry point
document.getElementById('btn-add-target').addEventListener('click', openDialog)

// Canvas right-click menu — power-user fallback
document.getElementById('ctx-add-target').addEventListener('click', () => {
  hideCtxMenu()
  openDialog()
})

// Close canvas menu on outside click / Escape
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
const fHypervisor   = document.getElementById('f-hypervisor')
const submitBtn     = document.getElementById('dialog-submit')

function openDialog() {
  fHostname.value   = ''
  fNickname.value   = ''
  fWgIp.value       = apiSuggestions.wg_ip
  fVirbr0Ip.value   = apiSuggestions.virbr0_ip
  fBackend.value    = 'kvm'
  fHypervisor.value = apiSuggestions.hypervisor ?? 'toshiba'
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

  const hostname   = fHostname.value.trim()
  const nickname   = fNickname.value.trim()
  const wg_ip      = fWgIp.value.trim()
  const virbr0_ip  = fVirbr0Ip.value.trim()
  const backend    = fBackend.value
  const hypervisor = fHypervisor.value.trim()

  try {
    await addHost({ hostname, nickname, virbr0_ip, wg_ip, backend, hypervisor })
    closeDialog()
    _addNodeToGraph({ hostname, nickname, virbr0_ip, wg_ip, backend })
    fetchHosts()
      .then(d => { apiSuggestions = d.suggestions })
      .catch(() => {})
  } catch (err) {
    dialogError.textContent = err.message
    dialogError.classList.remove('hidden')
    submitBtn.disabled    = false
    submitBtn.textContent = 'Add'
  }
})

function _addNodeToGraph({ hostname, wg_ip, virbr0_ip, backend }) {
  const pos = nextDevPosition(cy)
  cy.add({
    group: 'nodes',
    data: {
      id:            hostname,
      label:         `${hostname}\n[unprovisioned]`,
      role:          'spoke',
      platform:      backend,
      wg_ip,
      virbr0_ip,
      provisioned:   false,
      ansible_groups: ['kvm', 'targets', 'development', 'lab'],
      zone_id:       'zone-dev',
      parent:        'zone-dev',
    },
    position: pos,
  })

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
}

// ── Confirm destroy modal ─────────────────────────────────────────────────────

const confirmOverlay = document.getElementById('confirm-overlay')
const confirmBody    = document.getElementById('confirm-body')
let   _pendingDestroyHost = null

function showConfirmModal(hostname, provisioned = true) {
  _pendingDestroyHost = hostname
  confirmBody.textContent = provisioned
    ? `Destroy "${hostname}"?`
    : `Remove unprovisioned host "${hostname}"?`
  // Adjust the consequences list: unprovisioned = no VM to delete
  const vmConsequence = confirmOverlay.querySelector('.confirm-consequences li:first-child')
  if (vmConsequence) {
    vmConsequence.textContent = provisioned
      ? 'VM and disk permanently deleted'
      : 'No VM exists — config entries only'
  }
  confirmOverlay.classList.remove('hidden')
}

function hideConfirmModal() {
  confirmOverlay.classList.add('hidden')
  _pendingDestroyHost = null
}

document.getElementById('confirm-cancel').addEventListener('click', hideConfirmModal)

document.getElementById('confirm-submit').addEventListener('click', () => {
  const hostname = _pendingDestroyHost
  hideConfirmModal()
  _executeDestroy(hostname)
})

confirmOverlay.addEventListener('click', e => {
  if (e.target === confirmOverlay) hideConfirmModal()
})

// Warn if user tries to navigate/close the tab while a job is running
window.addEventListener('beforeunload', e => {
  if (activeJob) {
    e.preventDefault()
    e.returnValue = ''
  }
})

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
    cyEl.style.flex          = 'none'
    cyEl.style.height        = newCyH + 'px'
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
