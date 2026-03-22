import './style.css'
import cytoscape from 'cytoscape'
import { openPopup } from './popup.js'
import { registry } from './registry.js'
import { fetchHosts, fetchJobs, addHost, startProvision, startDestroy, pollJob } from './api.js'

// ── SVG icons ─────────────────────────────────────────────────────────────────
// base64-encoded SVGs used as Cytoscape background-image per node type.

function svgB64(svg) {
  return 'data:image/svg+xml;base64,' + btoa(svg)
}

// Standard dev/spoke VM — small computer monitor
const ICON_DEV = svgB64(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 56">' +
  '<rect x="4" y="6" width="56" height="38" rx="3" fill="#1a3a5a" stroke="#a0c4ff" stroke-width="2"/>' +
  '<rect x="7" y="9" width="50" height="32" rx="2" fill="#0a1520"/>' +
  '<rect x="22" y="44" width="20" height="5" fill="#2a4a6a"/>' +
  '<rect x="16" y="49" width="32" height="3" rx="1" fill="#2a4a6a"/>' +
  '</svg>'
)

// Master VM — rack server (3 rack units, more imposing)
const ICON_MASTER = svgB64(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 60">' +
  '<rect x="4" y="6"  width="56" height="13" rx="2" fill="#1a3a5a" stroke="#4fc3f7" stroke-width="2"/>' +
  '<rect x="4" y="21" width="56" height="13" rx="2" fill="#1a3a5a" stroke="#4fc3f7" stroke-width="2"/>' +
  '<rect x="4" y="36" width="56" height="13" rx="2" fill="#1a3a5a" stroke="#4fc3f7" stroke-width="2"/>' +
  '<circle cx="14" cy="12" r="3.5" fill="#4fc3f7"/>' +
  '<circle cx="14" cy="27" r="3.5" fill="#4fc3f7"/>' +
  '<circle cx="14" cy="42" r="3.5" fill="#4fc3f7"/>' +
  '<rect x="23" y="9"  width="30" height="7" rx="1" fill="#0a1520"/>' +
  '<rect x="23" y="24" width="30" height="7" rx="1" fill="#0a1520"/>' +
  '<rect x="23" y="39" width="30" height="7" rx="1" fill="#0a1520"/>' +
  '<rect x="18" y="52" width="28" height="6" rx="1" fill="#1a3a5a" stroke="#4fc3f7" stroke-width="1"/>' +
  '</svg>'
)

// Slave VM — stacked disk cylinders (replication storage)
const ICON_SLAVE = svgB64(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 60">' +
  '<ellipse cx="32" cy="13" rx="24" ry="7" fill="#163a2a" stroke="#66bb99" stroke-width="2"/>' +
  '<rect x="8" y="13" width="48" height="11" fill="#163a2a"/>' +
  '<line x1="8" y1="13" x2="8" y2="24" stroke="#66bb99" stroke-width="2"/>' +
  '<line x1="56" y1="13" x2="56" y2="24" stroke="#66bb99" stroke-width="2"/>' +
  '<ellipse cx="32" cy="24" rx="24" ry="7" fill="#0d2a1a" stroke="#66bb99" stroke-width="2"/>' +
  '<rect x="8" y="24" width="48" height="11" fill="#163a2a"/>' +
  '<line x1="8" y1="24" x2="8" y2="35" stroke="#66bb99" stroke-width="2"/>' +
  '<line x1="56" y1="24" x2="56" y2="35" stroke="#66bb99" stroke-width="2"/>' +
  '<ellipse cx="32" cy="35" rx="24" ry="7" fill="#0d2a1a" stroke="#66bb99" stroke-width="2"/>' +
  '<rect x="8" y="35" width="48" height="11" fill="#163a2a"/>' +
  '<line x1="8" y1="35" x2="8" y2="46" stroke="#66bb99" stroke-width="2"/>' +
  '<line x1="56" y1="35" x2="56" y2="46" stroke="#66bb99" stroke-width="2"/>' +
  '<ellipse cx="32" cy="46" rx="24" ry="7" fill="#0d2a1a" stroke="#66bb99" stroke-width="2"/>' +
  '</svg>'
)

// Stockroom template tile — spec sheet icon
const ICON_TEMPLATE = svgB64(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 50">' +
  '<rect x="3" y="3" width="54" height="44" rx="3" fill="#0d1b2e" stroke="#556677" stroke-width="1.5"/>' +
  '<rect x="3" y="3" width="54" height="15" rx="3" fill="#1a2535" stroke="#556677" stroke-width="1.5"/>' +
  '<rect x="3" y="10" width="54" height="8" fill="#1a2535"/>' +
  '<rect x="9" y="24" width="38" height="4" rx="1" fill="#2a3a4a"/>' +
  '<rect x="9" y="32" width="28" height="4" rx="1" fill="#2a3a4a"/>' +
  '<rect x="9" y="40" width="18" height="4" rx="1" fill="#1e2a38"/>' +
  '</svg>'
)

// ── Zone + template data ──────────────────────────────────────────────────────

const ZONE_DEFS = [
  { id: 'zone-console',    label: 'Console'     },
  { id: 'zone-dev',        label: 'Development' },
  { id: 'zone-staging',    label: 'Staging'     },
  { id: 'zone-production', label: 'Production'  },
]

const ZONE_GROUPS = {
  development: ['kvm', 'targets', 'development', 'lab'],
  staging:     ['kvm', 'targets', 'staging',     'lab'],
  production:  ['kvm', 'targets', 'production'],
}

// Stockroom: each entry is a VM class template with defaults for the Add dialog
const STOCKROOM_TEMPLATES = [
  { id: 'tpl-basic-vm', label: 'Basic VM\n2C / 2G / 20G',  defaultZone: 'development', defaultRole: 'dev'   },
  { id: 'tpl-mariadb',  label: 'MariaDB\n2C / 4G / 40G',   defaultZone: 'staging',     defaultRole: 'slave' },
  { id: 'tpl-erpnext',  label: 'ERPNext\n4C / 8G / 60G',   defaultZone: 'staging',     defaultRole: 'master'},
]

// Base positions for first node per zone (subsequent nodes spread right)
const ZONE_BASE_POS = {
  'zone-staging':    { baseX: 130, baseY: 650 },
  'zone-production': { baseX: 490, baseY: 650 },
}

// Initial positions for known nodes (absolute graph coordinates)
const INITIAL_POSITIONS = {
  controller:     { x: 110, y: 200 },
  saconsole:      { x: 110, y: 390 },
  target1:        { x: 500, y: 150 },
  target2:        { x: 660, y: 150 },
  tgt3:           { x: 500, y: 310 },
  target4:        { x: 660, y: 310 },
  'tpl-basic-vm': { x: 290, y: 180 },
  'tpl-mariadb':  { x: 290, y: 310 },
  'tpl-erpnext':  { x: 290, y: 440 },
}

function zoneFor(host) {
  if (host.wg_role === 'hub') return 'zone-console'
  const g = host.ansible_groups ?? []
  if (g.includes('production')) return 'zone-production'
  if (g.includes('staging'))    return 'zone-staging'
  return 'zone-dev'
}

function nextDevPosition(cy) {
  const devNodes = cy.nodes('[zone_id = "zone-dev"]')
  const xs = devNodes.map(n => n.position('x'))
  const maxX = xs.length ? Math.max(...xs) : 440
  return { x: maxX + 160, y: 150 }
}

function nextPositionForZone(cy, zoneId) {
  if (zoneId === 'zone-dev') return nextDevPosition(cy)
  const base    = ZONE_BASE_POS[zoneId] ?? { baseX: 500, baseY: 650 }
  const existing = cy.nodes(`[zone_id = "${zoneId}"]`)
  const xs       = existing.map(n => n.position('x'))
  const maxX     = xs.length ? Math.max(...xs) : base.baseX - 160
  return { x: maxX + 160, y: base.baseY }
}

// Count master/slave nodes in the given zone
function countZoneRoles(cy, zoneId) {
  if (!cy) return { masters: 0, slaves: 0 }
  return {
    masters: cy.nodes(`[zone_id = "${zoneId}"][vm_role = "master"]`).length,
    slaves:  cy.nodes(`[zone_id = "${zoneId}"][vm_role = "slave"]`).length,
  }
}

// ── Fallback topology (when API unreachable) ──────────────────────────────────

const FALLBACK_HOSTS = [
  { id: 'saconsole', hostname: 'saconsole', wg_role: 'hub',   wg_ip: '10.10.0.1', virbr0_ip: '192.168.122.10', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'development', 'lab'],            vm_role: 'dev' },
  { id: 'target1',   hostname: 'target1',   wg_role: 'spoke', wg_ip: '10.10.0.3', virbr0_ip: '192.168.122.11', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'targets', 'development', 'lab'], vm_role: 'dev' },
  { id: 'target2',   hostname: 'target2',   wg_role: 'spoke', wg_ip: '10.10.0.4', virbr0_ip: '192.168.122.12', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'targets', 'development', 'lab'], vm_role: 'dev' },
]

const CONTROLLER_HOST = {
  id: 'controller', hostname: 'controller', wg_role: 'controller',
  wg_ip: '10.10.0.2', virbr0_ip: '', backend: 'local',
  provisioned: true, ansible_groups: [], vm_role: 'dev',
}

// ── Graph data builder ────────────────────────────────────────────────────────

function buildNodesEdges(apiHosts) {
  const hosts    = apiHosts ?? FALLBACK_HOSTS
  const hub      = hosts.find(h => h.wg_role === 'hub')
  const allHosts = [CONTROLLER_HOST, ...hosts]

  const zoneNodes = ZONE_DEFS.map(z => ({
    data: { id: z.id, label: z.label, zone: true },
  }))

  // Stockroom compound node (child of zone-console)
  const stockroomNode = {
    data: { id: 'stockroom', label: 'Stockroom', parent: 'zone-console', stockroom: true },
  }

  // Template tiles — children of stockroom, click to pre-fill Add dialog
  const templateNodes = STOCKROOM_TEMPLATES.map(tpl => ({
    data: {
      id:          tpl.id,
      label:       tpl.label,
      template:    true,
      defaultZone: tpl.defaultZone,
      defaultRole: tpl.defaultRole,
      parent:      'stockroom',
    },
    position: INITIAL_POSITIONS[tpl.id],
  }))

  const vmNodes = allHosts.map(h => {
    const zone = h.wg_role === 'controller' ? 'zone-console' : zoneFor(h)
    return {
      data: {
        id:             h.id ?? h.hostname,
        label:          h.provisioned === false ? `${h.hostname}\n[unprovisioned]`
                      : h.provisioned === null  ? `${h.hostname}\n[unknown]`
                      : h.hostname,
        role:           h.wg_role,
        vm_role:        h.vm_role ?? 'dev',
        platform:       h.backend ?? 'kvm',
        wg_ip:          h.wg_ip     ?? '',
        virbr0_ip:      h.virbr0_ip ?? '',
        provisioned:    !!h.provisioned,
        ansible_groups: h.ansible_groups ?? [],
        zone_id:        zone,
        parent:         zone,
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

  return { nodes: [...zoneNodes, stockroomNode, ...templateNodes, ...vmNodes], edges }
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
      'events':             'no',
    }
  },
  { selector: '#zone-console',    style: { 'border-color': '#888888', 'color': '#aaaaaa' } },
  { selector: '#zone-dev',        style: { 'border-color': '#44aa66', 'color': '#44aa66' } },
  { selector: '#zone-staging',    style: { 'border-color': '#cc8833', 'color': '#cc8833' } },
  { selector: '#zone-production', style: { 'border-color': '#cc4444', 'color': '#cc4444' } },

  // ── Stockroom compound ──
  {
    selector: 'node[stockroom]',
    style: {
      'shape':              'rectangle',
      'background-color':   '#0d1520',
      'background-opacity': 0.7,
      'border-color':       '#445566',
      'border-width':       1,
      'border-style':       'dashed',
      'label':              'data(label)',
      'text-valign':        'top',
      'text-halign':        'center',
      'font-family':        'monospace',
      'font-size':          '10px',
      'color':              '#556677',
      'padding':            '18px',
      'events':             'no',
    }
  },

  // ── Template tiles (click → pre-fill Add dialog) ──
  {
    selector: 'node[template]',
    style: {
      'shape':              'rectangle',
      'background-image':   ICON_TEMPLATE,
      'background-fit':     'contain',
      'background-opacity': 0,
      'border-width':       1,
      'border-color':       '#445566',
      'border-style':       'solid',
      'label':              'data(label)',
      'color':              '#778899',
      'font-family':        'monospace',
      'font-size':          '8px',
      'text-valign':        'bottom',
      'text-halign':        'center',
      'text-margin-y':      6,
      'text-wrap':          'wrap',
      'width':              62,
      'height':             52,
      'cursor':             'pointer',
    }
  },
  {
    selector: 'node[template]:hover',
    style: { 'border-color': '#8899aa', 'color': '#99aabb' }
  },

  // ── VM / controller nodes — base ──
  {
    selector: 'node:not([zone]):not([template]):not([stockroom])',
    style: {
      'shape':              'rectangle',
      'background-opacity': 0,
      'border-width':       1,
      'border-color':       '#a0c4ff',
      'label':              'data(label)',
      'color':              '#e0e0e0',
      'font-family':        'monospace',
      'font-size':          '11px',
      'text-valign':        'bottom',
      'text-halign':        'center',
      'text-margin-y':      6,
      'text-wrap':          'wrap',
      'width':              80,
      'height':             70,
    }
  },

  // ── Icons by vm_role ──
  {
    selector: 'node[vm_role = "dev"]:not([template])',
    style: {
      'background-image': ICON_DEV,
      'background-fit':   'contain',
    }
  },
  {
    selector: 'node[vm_role = "master"]',
    style: {
      'background-image': ICON_MASTER,
      'background-fit':   'contain',
      'border-color':     '#4fc3f7',
      'border-width':     2,
      'width':            90,
      'height':           80,
    }
  },
  {
    selector: 'node[vm_role = "slave"]',
    style: {
      'background-image': ICON_SLAVE,
      'background-fit':   'contain',
      'border-color':     '#66bb99',
      'border-width':     2,
      'height':           80,
    }
  },

  // ── Special roles override ──
  {
    selector: 'node[role = "hub"]',
    style: {
      'border-color': '#4fc3f7',
      'border-width': 2,
      'border-style': 'double',
      'width':        90,
      'height':       80,
    }
  },
  {
    selector: 'node[role = "controller"]',
    style: {
      'border-color': '#c8e6a0',
      'border-style': 'dashed',
    }
  },

  // ── Unprovisioned state ──
  {
    selector: 'node[!provisioned]:not([template]):not([stockroom])',
    style: {
      'border-color': '#f0a020',
      'border-width': 2,
      'border-style': 'dashed',
    }
  },

  // ── Selected ──
  {
    selector: 'node:selected:not([zone]):not([stockroom])',
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
    const data     = await fetchHosts()
    hosts          = data.hosts
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
      positions: node => INITIAL_POSITIONS[node.id()] || undefined,
    },
  })

  cy.fit(cy.elements(), 60)
  attachHandlers()
  _updatePromoteButton()
  _reconnectActiveJob()
}

// ── Info panel ────────────────────────────────────────────────────────────────

const infoPanel = document.getElementById('info-panel')

function hint(msg) {
  infoPanel.innerHTML = `<p class="hint">${msg}</p>`
}

function renderInfo(data) {
  const skip = new Set(['id', 'zone', 'ansible_groups', 'zone_id', 'template', 'stockroom', 'defaultZone', 'defaultRole'])
  const rows = Object.entries(data)
    .filter(([k]) => !skip.has(k))
    .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
    .join('')
  infoPanel.innerHTML = `<table>${rows}</table>`
}

// Render info + contextual action buttons for this VM node.
// No-ops while a job is running (don't overwrite the job log).
function renderInfoWithActions(data) {
  if (activeJob) return
  renderInfo(data)

  const role        = data.role
  const provisioned = data.provisioned
  const vm_role     = data.vm_role ?? 'dev'
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

  // Clone to Staging — only for provisioned dev spokes
  if (isOperational && provisioned && vm_role === 'dev' && data.zone_id === 'zone-dev') {
    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--clone'
    btn.textContent = 'Clone to Staging'
    btn.title       = 'Deploy a new VM in Staging (fresh provision — not a disk copy)'
    btn.onclick     = () => openDialogForZone('staging', data.id)
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

// Render info + Deploy button for a Stockroom template tile
function renderTemplateInfo(data) {
  const title = data.label.replace('\n', ' — ')
  infoPanel.innerHTML =
    `<p class="hint"><strong>${title}</strong></p>` +
    `<p class="hint" style="margin-top:6px">Click <em>Deploy from Template</em> to add a VM pre-configured for this role.</p>`

  const actions = document.createElement('div')
  actions.className = 'action-bar'
  const btn = document.createElement('button')
  btn.className   = 'action-btn'
  btn.textContent = 'Deploy from Template'
  btn.onclick     = () => openDialogFromTemplate(data)
  actions.appendChild(btn)
  infoPanel.appendChild(actions)
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

// ── Promote button ────────────────────────────────────────────────────────────

const btnPromote = document.getElementById('btn-promote')

function _updatePromoteButton() {
  if (!cy) { btnPromote.disabled = true; return }
  const { masters, slaves } = countZoneRoles(cy, 'zone-staging')
  const ready = masters === 1 && slaves === 1
  btnPromote.disabled = !ready
  btnPromote.title = ready
    ? 'Promote Staging → Production (1 Master + 1 Slave ready)'
    : `Promote Staging → Production — requires exactly 1 Master + 1 Slave in Staging (found ${masters}M ${slaves}S)`
}

btnPromote.addEventListener('click', () => {
  if (btnPromote.disabled) return
  showPromoteModal()
})

// ── Promote modal ─────────────────────────────────────────────────────────────

const promoteOverlay = document.getElementById('promote-overlay')

function showPromoteModal() {
  const { masters, slaves } = countZoneRoles(cy, 'zone-staging')
  document.getElementById('promote-staging-status').innerHTML =
    `<p>${masters === 1 ? '✅' : '❌'} Staging Master: ${masters}</p>` +
    `<p>${slaves  === 1 ? '✅' : '❌'} Staging Slave:  ${slaves}</p>`
  promoteOverlay.classList.remove('hidden')
}

function hidePromoteModal() {
  promoteOverlay.classList.add('hidden')
}

document.getElementById('promote-cancel').addEventListener('click', hidePromoteModal)

promoteOverlay.addEventListener('click', e => {
  if (e.target === promoteOverlay) hidePromoteModal()
})

document.getElementById('promote-submit').addEventListener('click', async () => {
  try {
    await fetch('/api/promote', { method: 'POST' })
    hidePromoteModal()
    hint('Promotion initiated — awaiting Telegram approval from 2 administrators. (DNS flip not yet implemented.)')
  } catch {
    hint('Could not reach API to initiate promotion.')
  }
})

// ── Provision flow ────────────────────────────────────────────────────────────

const JOB_KEY  = 'esacp_active_job'
let   activeJob = null  // { job_id, hostname, type } — set while a job is in progress

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

function runDestroy(hostname, provisioned = true) {
  showConfirmModal(hostname, provisioned)
}

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
          const node = cy.$(`#${hostname}`)
          cy.remove(node.connectedEdges())
          cy.remove(node)
          hint('Node destroyed. Use + Add Target to register a new VM.')
        }
      }
      _updatePromoteButton()
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
  // Template tile click → show Deploy button
  cy.on('tap', 'node[template]', evt => {
    renderTemplateInfo(evt.target.data())
  })

  // VM node click → info + action buttons
  cy.on('tap', 'node:not([zone]):not([template]):not([stockroom])', evt => {
    renderInfoWithActions(evt.target.data())
  })

  // Edge click → info only
  cy.on('tap', 'edge', evt => {
    if (activeJob) return
    renderInfo(evt.target.data())
  })

  // Canvas tap → hint
  cy.on('tap', evt => {
    if (evt.target === cy) {
      if (activeJob) return
      hint('Click a node to inspect it. Use + Add Target in the toolbar.')
    }
  })

  // Canvas right-click → shortcut menu
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

document.getElementById('btn-add-target').addEventListener('click', openDialog)

document.getElementById('ctx-add-target').addEventListener('click', () => {
  hideCtxMenu()
  openDialog()
})

document.addEventListener('click', e => {
  if (!ctxMenu.contains(e.target)) hideCtxMenu()
})

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    hideCtxMenu()
    hideConfirmModal()
    hidePromoteModal()
    closeDialog()
  }
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
const fZone         = document.getElementById('f-zone')
const fVmRole       = document.getElementById('f-vm-role')
const submitBtn     = document.getElementById('dialog-submit')
const fieldVmRole   = document.getElementById('field-vm-role')

// Enforce 1M+1S slot limits; show/hide Role field based on Zone selection.
function _refreshRoleOptions() {
  const zone = fZone.value
  if (zone === 'development') {
    fieldVmRole.style.display = 'none'
    fVmRole.value = 'dev'
    dialogError.classList.add('hidden')
    submitBtn.disabled    = false
    submitBtn.textContent = 'Add'
    return
  }

  fieldVmRole.style.display = 'block'
  const zoneId    = zone === 'staging' ? 'zone-staging' : 'zone-production'
  const { masters, slaves } = countZoneRoles(cy, zoneId)
  const masterOpt = fVmRole.querySelector('option[value="master"]')
  const slaveOpt  = fVmRole.querySelector('option[value="slave"]')
  const devOpt    = fVmRole.querySelector('option[value="dev"]')

  masterOpt.disabled = masters >= 1
  slaveOpt.disabled  = slaves  >= 1
  devOpt.disabled    = true   // dev role not valid in staging/production

  if (masterOpt.disabled && slaveOpt.disabled) {
    dialogError.textContent = `${zone.charAt(0).toUpperCase() + zone.slice(1)} zone is full (1 Master + 1 Slave). Destroy a VM first.`
    dialogError.classList.remove('hidden')
    submitBtn.disabled    = true
    submitBtn.textContent = 'Add'
  } else {
    dialogError.classList.add('hidden')
    submitBtn.disabled    = false
    submitBtn.textContent = 'Add'
    if (fVmRole.value === 'dev' || (fVmRole.value === 'master' && masterOpt.disabled)) {
      fVmRole.value = !masterOpt.disabled ? 'master' : 'slave'
    }
  }
}

fZone.addEventListener('change', _refreshRoleOptions)

function openDialog(opts = {}) {
  fHostname.value   = opts.hostname   ?? ''
  fNickname.value   = ''
  fWgIp.value       = apiSuggestions.wg_ip
  fVirbr0Ip.value   = apiSuggestions.virbr0_ip
  fBackend.value    = 'kvm'
  fHypervisor.value = apiSuggestions.hypervisor ?? 'toshiba'
  fZone.value       = opts.zone    ?? 'development'
  fVmRole.value     = opts.vm_role ?? 'dev'
  dialogError.classList.add('hidden')
  dialogError.textContent = ''
  submitBtn.disabled    = false
  submitBtn.textContent = 'Add'
  _refreshRoleOptions()
  dialogOverlay.classList.remove('hidden')
  fHostname.focus()
}

function closeDialog() {
  dialogOverlay.classList.add('hidden')
}

// Open dialog pre-filled from a Stockroom template tile
function openDialogFromTemplate(tplData) {
  openDialog({ zone: tplData.defaultZone, vm_role: tplData.defaultRole })
}

// Open dialog pre-filled for a target zone (e.g. Clone to Staging)
function openDialogForZone(zone, sourceHostname) {
  openDialog({ zone })
  if (sourceHostname) fHostname.placeholder = `${sourceHostname}-staging`
}

document.getElementById('dialog-cancel').addEventListener('click', closeDialog)

dialogOverlay.addEventListener('click', e => {
  if (e.target === dialogOverlay) closeDialog()
})

document.getElementById('add-target-form').addEventListener('submit', async e => {
  e.preventDefault()
  dialogError.classList.add('hidden')
  submitBtn.disabled    = true
  submitBtn.textContent = 'Adding…'

  const hostname   = fHostname.value.trim()
  const nickname   = fNickname.value.trim()
  const wg_ip      = fWgIp.value.trim()
  const virbr0_ip  = fVirbr0Ip.value.trim()
  const backend    = fBackend.value
  const hypervisor = fHypervisor.value.trim()
  const zone       = fZone.value
  const vm_role    = zone === 'development' ? 'dev' : fVmRole.value

  try {
    await addHost({ hostname, nickname, virbr0_ip, wg_ip, backend, hypervisor, zone, vm_role })
    closeDialog()
    _addNodeToGraph({ hostname, wg_ip, virbr0_ip, backend, zone, vm_role })
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

function _zoneIdFor(zone) {
  if (zone === 'staging')    return 'zone-staging'
  if (zone === 'production') return 'zone-production'
  return 'zone-dev'
}

function _addNodeToGraph({ hostname, wg_ip, virbr0_ip, backend, zone = 'development', vm_role = 'dev' }) {
  const zoneId = _zoneIdFor(zone)
  const pos    = nextPositionForZone(cy, zoneId)
  const groups = ZONE_GROUPS[zone] ?? ZONE_GROUPS.development

  cy.add({
    group: 'nodes',
    data: {
      id:             hostname,
      label:          `${hostname}\n[unprovisioned]`,
      role:           'spoke',
      vm_role,
      platform:       backend,
      wg_ip,
      virbr0_ip,
      provisioned:    false,
      ansible_groups: groups,
      zone_id:        zoneId,
      parent:         zoneId,
    },
    position: pos,
  })

  const hub = cy.nodes('[role = "hub"]').first()
  if (hub.length) {
    cy.add({
      group: 'edges',
      data: { id: `wg-${hostname}`, source: hub.id(), target: hostname, label: 'WireGuard', type: 'wireguard' },
    })
  }

  _updatePromoteButton()
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

// ── beforeunload guard ────────────────────────────────────────────────────────

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
