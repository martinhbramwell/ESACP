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

// Outer boundary of the 4-zone area in graph coordinates.
// All INITIAL_POSITIONS for real VMs must fall inside this box.
const ZONE_GRAPH = { LEFT: 60, RIGHT: 870, TOP: 50, BOTTOM: 730 }

// Base positions for the first non-anchor node per zone (subsequent nodes spread right)
const ZONE_BASE_POS = {
  'zone-staging':    { baseX: 120, baseY: 600 },
  'zone-production': { baseX: 540, baseY: 600 },
}

// Invisible anchor nodes placed at the corners of each quadrant.
// They force each compound zone to occupy its intended screen area even when empty.
// Style: width/height 1, fully transparent, no events.
const ZONE_ANCHORS = [
  // Console (top-left)
  { id: 'anch-con-a', zone: 'zone-console',    x: 60,  y: 50  },
  { id: 'anch-con-b', zone: 'zone-console',    x: 390, y: 380 },
  // Development (top-right)
  { id: 'anch-dev-a', zone: 'zone-dev',        x: 460, y: 50  },
  { id: 'anch-dev-b', zone: 'zone-dev',        x: 870, y: 380 },
  // Staging (bottom-left)
  { id: 'anch-stg-a', zone: 'zone-staging',    x: 60,  y: 470 },
  { id: 'anch-stg-b', zone: 'zone-staging',    x: 390, y: 730 },
  // Production (bottom-right)
  { id: 'anch-pro-a', zone: 'zone-production', x: 460, y: 470 },
  { id: 'anch-pro-b', zone: 'zone-production', x: 870, y: 730 },
]

// Initial positions for known nodes (absolute graph coordinates).
// All positions are chosen to fall within their zone's quadrant boundary.
const INITIAL_POSITIONS = {
  // Console quadrant (TL): x 60-390, y 50-380
  controller:     { x: 120, y: 150 },
  saconsole:      { x: 120, y: 280 },
  'tpl-basic-vm': { x: 300, y: 115 },
  'tpl-mariadb':  { x: 300, y: 215 },
  'tpl-erpnext':  { x: 300, y: 315 },
  // Development quadrant (TR): x 460-870, y 50-380
  target1:        { x: 540, y: 150 },
  target2:        { x: 710, y: 150 },
  tgt3:           { x: 540, y: 300 },
  target4:        { x: 710, y: 300 },
}

function zoneFor(host) {
  if (host.wg_role === 'hub') return 'zone-console'
  const g = host.ansible_groups ?? []
  if (g.includes('production')) return 'zone-production'
  if (g.includes('staging'))    return 'zone-staging'
  return 'zone-dev'
}

function nextDevPosition(cy) {
  const devNodes = cy.nodes('[zone_id = "zone-dev"]:not(.phantom)')
  const xs = devNodes.map(n => n.position('x'))
  const maxX = xs.length ? Math.max(...xs) : 440
  return { x: maxX + 160, y: 150 }
}

function nextPositionForZone(cy, zoneId) {
  if (zoneId === 'zone-dev') return nextDevPosition(cy)
  const base     = ZONE_BASE_POS[zoneId] ?? { baseX: 500, baseY: 650 }
  const existing = cy.nodes(`[zone_id = "${zoneId}"]:not(.phantom)`)
  const xs       = existing.map(n => n.position('x'))
  const maxX     = xs.length ? Math.max(...xs) : base.baseX - 160
  return { x: maxX + 160, y: base.baseY }
}

// Count master/slave nodes in the given zone
function countZoneRoles(cy, zoneId) {
  if (!cy) return { masters: 0, slaves: 0 }
  return {
    masters: cy.nodes(`[zone_id = "${zoneId}"][vm_role = "master"]:not(.phantom)`).length,
    slaves:  cy.nodes(`[zone_id = "${zoneId}"][vm_role = "slave"]:not(.phantom)`).length,
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

  // Zone boundaries are HTML overlays — no Cytoscape compound nodes.
  // Template tiles are top-level nodes (no parent/stockroom compound).
  const templateNodes = STOCKROOM_TEMPLATES.map(tpl => ({
    data: {
      id:          tpl.id,
      label:       tpl.label,
      template:    'yes',
      provisioned: true,   // prevents unprovisioned amber-dashed style
      defaultZone: tpl.defaultZone,
      defaultRole: tpl.defaultRole,
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

  // Invisible anchor nodes — top-level, define graph extent for cy.fit().
  // provisioned:true prevents the unprovisioned amber-dashed selector from matching.
  const anchorNodes = ZONE_ANCHORS.map(a => ({
    data: { id: a.id, phantom: 'yes', label: '', provisioned: true },
    position: { x: a.x, y: a.y },
  }))

  return { nodes: [...templateNodes, ...vmNodes, ...anchorNodes], edges }
}

// ── Cytoscape styles ──────────────────────────────────────────────────────────

const CY_STYLE = [
  // ── Template tiles (Stockroom) ──
  {
    selector: 'node.template-node',
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
    selector: 'node.template-node:hover',
    style: { 'border-color': '#8899aa', 'color': '#99aabb' }
  },

  // ── VM / controller nodes ──
  {
    selector: 'node:not(.template-node):not(.phantom)',
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
    selector: 'node[vm_role = "dev"]:not(.template-node)',
    style: { 'background-image': ICON_DEV, 'background-fit': 'contain' }
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

  // ── Special roles ──
  {
    selector: 'node[role = "hub"]',
    style: { 'border-color': '#4fc3f7', 'border-width': 3, 'width': 70, 'height': 60 }
  },
  {
    selector: 'node[role = "controller"]',
    style: { 'border-color': '#c8e6a0', 'border-style': 'dashed' }
  },

  // ── Unprovisioned ──
  {
    selector: 'node[!provisioned]:not(.template-node):not(.phantom)',
    style: { 'border-color': '#f0a020', 'border-width': 2, 'border-style': 'dashed' }
  },

  // ── Phantom anchor nodes — MUST come after all VM styles to win on specificity tie ──
  // node.phantom[phantom="yes"] = class(10) + attr(10) + element(1) = 21
  // Same specificity as base VM style but LATER in array → wins.
  // Also immune to unprovisioned selector because provisioned:true is set in data.
  {
    selector: 'node.phantom[phantom = "yes"]',
    style: {
      'width':              1,
      'height':             1,
      'background-opacity': 0,
      'border-width':       0,
      'label':              '',
      'events':             'no',
    }
  },

  // ── Selected ──
  {
    selector: 'node:selected:not(.phantom)',
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

  // Apply CSS classes — class selectors are reliable; [attr] existence selectors
  // have a bug in Cytoscape 3.33.x where boolean/truthy values don't match.
  ZONE_ANCHORS.forEach(a      => cy.$('#' + a.id).addClass('phantom'))
  STOCKROOM_TEMPLATES.forEach(t => cy.$('#' + t.id).addClass('template-node'))

  cy.fit(cy.elements(), 60)
  attachHandlers()
  _updatePromoteButton()
  _reconnectActiveJob()

  // Position zone overlay panels and splitter; keep in sync with pan/zoom/resize
  _updateZoneOverlay()
  cy.on('pan zoom resize', _updateZoneOverlay)
}

// ── Quad-zone splitter ────────────────────────────────────────────────────────
// A draggable "+" handle at the intersection of the 4 quadrants.
// Dragging it resizes the quadrants by moving the phantom anchor nodes.

let splitX = 425   // initial graph-coordinate split point (matches ZONE_GRAPH midpoint)
let splitY = 425

function _updateQuadAnchors(rawX, rawY) {
  // Clamp so each zone keeps at least 80 graph units of usable width/height.
  // Writes back to module-level splitX/splitY so _updateZoneOverlay reads
  // the same clamped values.
  const { LEFT, RIGHT, TOP, BOTTOM } = ZONE_GRAPH
  splitX = Math.max(LEFT  + 80, Math.min(RIGHT  - 80, rawX))
  splitY = Math.max(TOP   + 80, Math.min(BOTTOM - 80, rawY))

  cy.$('#anch-con-a').position({ x: LEFT,   y: TOP    })
  cy.$('#anch-con-b').position({ x: splitX, y: splitY })
  cy.$('#anch-dev-a').position({ x: splitX, y: TOP    })
  cy.$('#anch-dev-b').position({ x: RIGHT,  y: splitY })
  cy.$('#anch-stg-a').position({ x: LEFT,   y: splitY })
  cy.$('#anch-stg-b').position({ x: splitX, y: BOTTOM })
  cy.$('#anch-pro-a').position({ x: splitX, y: splitY })
  cy.$('#anch-pro-b').position({ x: RIGHT,  y: BOTTOM })

  // Fences squeeze sheep: push every VM inside its zone's new bounds.
  _constrainVMsToZones()
}

// Minimum clearance (graph units) between a VM centre and its zone fence.
const ZONE_VM_MARGIN = 50

function _constrainVMsToZones() {
  if (!cy) return
  const { LEFT, RIGHT, TOP, BOTTOM } = ZONE_GRAPH
  const m = ZONE_VM_MARGIN
  const bounds = {
    'zone-console':    { x1: LEFT,   y1: TOP,    x2: splitX, y2: splitY },
    'zone-dev':        { x1: splitX, y1: TOP,    x2: RIGHT,  y2: splitY },
    'zone-staging':    { x1: LEFT,   y1: splitY, x2: splitX, y2: BOTTOM },
    'zone-production': { x1: splitX, y1: splitY, x2: RIGHT,  y2: BOTTOM },
  }
  cy.nodes(':not(.phantom):not(.template-node)').forEach(node => {
    const b = bounds[node.data('zone_id')]
    if (!b) return
    const pos = node.position()
    const nx  = Math.max(b.x1 + m, Math.min(b.x2 - m, pos.x))
    const ny  = Math.max(b.y1 + m, Math.min(b.y2 - m, pos.y))
    if (nx !== pos.x || ny !== pos.y) node.position({ x: nx, y: ny })
  })
}

function _graphToScreen(gx, gy) {
  const pan = cy.pan(), zoom = cy.zoom()
  return { x: gx * zoom + pan.x, y: gy * zoom + pan.y }
}

// Stockroom bounding box in graph coordinates (surrounds the 3 template tiles)
const STOCKROOM_GRAPH = { x1: 258, y1: 78, x2: 362, y2: 362 }

function _updateZoneOverlay() {
  if (!cy) return
  // All geometry derived from the same two values (splitX, splitY) via _graphToScreen().
  // This guarantees zone frames, splitter handle, and _zoneAtPos() are all consistent
  // with each other and with where Cytoscape actually renders VM nodes.
  const { LEFT, RIGHT, TOP, BOTTOM } = ZONE_GRAPH
  const tl = _graphToScreen(LEFT,   TOP)     // outer top-left
  const br = _graphToScreen(RIGHT,  BOTTOM)  // outer bottom-right
  const sp = _graphToScreen(splitX, splitY)  // cross-hair point

  const panels = {
    'panel-console':    { x1: tl.x, y1: tl.y, x2: sp.x, y2: sp.y },
    'panel-dev':        { x1: sp.x, y1: tl.y, x2: br.x, y2: sp.y },
    'panel-staging':    { x1: tl.x, y1: sp.y, x2: sp.x, y2: br.y },
    'panel-production': { x1: sp.x, y1: sp.y, x2: br.x, y2: br.y },
  }
  for (const [id, { x1, y1, x2, y2 }] of Object.entries(panels)) {
    const el = document.getElementById(id)
    if (!el) continue
    el.style.left   = x1 + 'px'
    el.style.top    = y1 + 'px'
    el.style.width  = (x2 - x1) + 'px'
    el.style.height = (y2 - y1) + 'px'
  }

  const sr1 = _graphToScreen(STOCKROOM_GRAPH.x1, STOCKROOM_GRAPH.y1)
  const sr2 = _graphToScreen(STOCKROOM_GRAPH.x2, STOCKROOM_GRAPH.y2)
  const stockEl = document.getElementById('stockroom-panel')
  if (stockEl) {
    stockEl.style.left   = sr1.x + 'px'
    stockEl.style.top    = sr1.y + 'px'
    stockEl.style.width  = (sr2.x - sr1.x) + 'px'
    stockEl.style.height = (sr2.y - sr1.y) + 'px'
  }

  const splitterEl = document.getElementById('quad-splitter')
  if (splitterEl) {
    splitterEl.style.left = sp.x + 'px'
    splitterEl.style.top  = sp.y + 'px'
  }
}

;(function _initSplitter() {
  const el   = document.getElementById('quad-splitter')
  const cyEl = document.getElementById('cy')
  if (!el) return

  let dragging = false

  el.addEventListener('mousedown', e => {
    e.preventDefault()
    e.stopPropagation()
    dragging = true
    el.classList.add('dragging')
    if (cy) { cy.userPanningEnabled(false); cy.userZoomingEnabled(false) }
  })

  document.addEventListener('mousemove', e => {
    if (!dragging) return
    const rect  = cyEl.getBoundingClientRect()
    const pan   = cy.pan()
    const zoom  = cy.zoom()
    const rawX  = (e.clientX - rect.left - pan.x) / zoom
    const rawY  = (e.clientY - rect.top  - pan.y) / zoom
    _updateQuadAnchors(rawX, rawY)  // clamps and writes back to splitX, splitY
    _updateZoneOverlay()            // reads clamped splitX, splitY
  })

  document.addEventListener('mouseup', () => {
    if (!dragging) return
    dragging = false
    el.classList.remove('dragging')
    if (cy) { cy.userPanningEnabled(true); cy.userZoomingEnabled(true) }
  })
})()

// ── Zone-change on drag ───────────────────────────────────────────────────────
// Dragging a VM across a zone fence reassigns it to the new paddock.
// Zone boundaries are the same splitX/splitY values used to draw the fence —
// guaranteed consistent with zone frame positions and VM rendered positions.

function _zoneAtPos(pos) {
  const { LEFT, RIGHT, TOP, BOTTOM } = ZONE_GRAPH
  if (pos.x < LEFT || pos.x > RIGHT || pos.y < TOP || pos.y > BOTTOM) return null
  const onLeft = pos.x <= splitX, onTop = pos.y <= splitY
  if (onLeft  &&  onTop) return 'zone-console'
  if (!onLeft &&  onTop) return 'zone-dev'
  if (onLeft  && !onTop) return 'zone-staging'
  return 'zone-production'
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
  cy.on('tap', 'node.template-node', evt => {
    renderTemplateInfo(evt.target.data())
  })

  // VM node click → info + action buttons
  cy.on('tap', 'node:not(.template-node):not(.phantom)', evt => {
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
    if (evt.target === cy) {
      const { x, y } = evt.originalEvent
      showCtxMenu(x, y)
    }
  })

  // ── Drag-to-rezone: sheep crossing a fence changes paddock ──
  const _preDragPos = new Map()

  // Record position before drag begins (needed for snap-back on rejected drops)
  cy.on('grab', 'node:not(.phantom):not(.template-node)', evt => {
    const n = evt.target
    _preDragPos.set(n.id(), { ...n.position() })
  })

  // On drop: detect which zone the node landed in; reassign or reject
  cy.on('dragfree', 'node:not(.phantom):not(.template-node)', evt => {
    const node = evt.target
    const role = node.data('role')

    const pos       = node.position()
    const newZoneId = _zoneAtPos(pos)
    const oldZoneId = node.data('zone_id')

    function snapBack() {
      const prev = _preDragPos.get(node.id())
      if (prev) node.position(prev)
      _preDragPos.delete(node.id())
    }

    // Hub and controller are permanent Console residents — always snap back
    if (role === 'hub' || role === 'controller') { snapBack(); return }

    // Dropped outside all fences — return to paddock
    if (!newZoneId) { snapBack(); return }

    // Console is reserved for hub/controller — reject
    if (newZoneId === 'zone-console') { snapBack(); return }

    // Production is write-protected — only reachable via the Promote button
    if (newZoneId === 'zone-production') {
      hint('Production zone is write-protected. Use the Promote → button.')
      snapBack()
      return
    }

    // Still in same paddock — fine, keep position
    if (newZoneId === oldZoneId) { _preDragPos.delete(node.id()); return }

    // Crossed a fence — determine new role.
    // node.data('zone_id') is still oldZoneId at this point, so counting newZoneId
    // naturally excludes the dragged node.
    let newRole = 'dev'
    if (newZoneId === 'zone-staging' || newZoneId === 'zone-production') {
      const inNewZone      = cy.nodes(`[zone_id = "${newZoneId}"]:not(.phantom)`)
      const existingMasters = inNewZone.filter('[vm_role = "master"]').length
      const existingSlaves  = inNewZone.filter('[vm_role = "slave"]').length

      if      (existingMasters < 1) newRole = 'master'
      else if (existingSlaves  < 1) newRole = 'slave'
      else {
        const zoneName = newZoneId === 'zone-staging' ? 'Staging' : 'Production'
        hint(`${zoneName} zone is full (1 Master + 1 Slave). Remove a VM first.`)
        snapBack()
        return
      }
    }

    node.data('zone_id', newZoneId)
    node.data('vm_role', newRole)
    _preDragPos.delete(node.id())
    _updatePromoteButton()
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
