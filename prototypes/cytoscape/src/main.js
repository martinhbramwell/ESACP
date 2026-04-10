import './style.css'
import cytoscape from 'cytoscape'
import { openPopup } from './popup.js'
import { registry } from './registry.js'
import { fetchHosts, fetchJobs, addHost, startProvision, startProvisionErpnext, startDestroy, pollJob, fetchTemplateStatus, startBuildTemplate, deleteTemplate, startRefresh, startVm, stopVm, rebootVm } from './api.js'

// ── SVG icons ─────────────────────────────────────────────────────────────────
// base64-encoded SVGs used as Cytoscape background-image per node type.

function svgB64(svg) {
  return 'data:image/svg+xml;base64,' + btoa(svg)
}

// Standard dev/spoke VM — small computer monitor
// width/height MUST match the viewBox so Cytoscape's background-fit:contain uses
// the correct aspect ratio. Without them the browser defaults to 300×150 intrinsic.
const ICON_DEV = svgB64(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 56" width="64" height="56">' +
  '<rect x="4" y="6" width="56" height="38" rx="3" fill="#1a3a5a" stroke="#a0c4ff" stroke-width="2"/>' +
  '<rect x="7" y="9" width="50" height="32" rx="2" fill="#0a1520"/>' +
  '<rect x="22" y="44" width="20" height="5" fill="#2a4a6a"/>' +
  '<rect x="16" y="49" width="32" height="3" rx="1" fill="#2a4a6a"/>' +
  '</svg>'
)

// Master VM — rack server (3 rack units, more imposing)
const ICON_MASTER = svgB64(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 60" width="64" height="60">' +
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
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 60" width="64" height="60">' +
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
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 50" width="60" height="50">' +
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

// Stockroom: ERPNext tile only. Visibility controlled by tpl-none/tpl-building/tpl-ready class.
const STOCKROOM_TEMPLATES = [
  { id: 'tpl-erpnext', label: 'ERPNext\n4C / 8G / 60G', defaultZone: 'staging', defaultRole: 'master' },
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
  // Stockroom (single ERPNext tile) on the left; controller + saconsole on the right
  'tpl-erpnext': { x: 160, y: 220 },
  controller:     { x: 330, y: 150 },
  saconsole:      { x: 330, y: 280 },
  // Development quadrant (TR): x 460-870, y 50-380
  target1:        { x: 540, y: 150 },
  target2:        { x: 710, y: 150 },
  target3:        { x: 540, y: 310 },
  target4:        { x: 710, y: 310 },
}

function zoneFor(host) {
  if (host.wg_role === 'hub') return 'zone-console'
  const g = host.ansible_groups ?? []
  if (g.includes('production')) return 'zone-production'
  if (g.includes('staging'))    return 'zone-staging'
  return 'zone-dev'
}

// Normalise API single-word vm_role to the two-part "zone:type" format.
// Old API values: 'dev', 'master', 'slave' → new: 'dev:unspecified', 'staging:master', etc.
function normalizeVmRole(rawRole, zoneId) {
  if (!rawRole || rawRole === 'dev') return 'dev:unspecified'
  const zone = zoneId.replace('zone-', '')  // 'dev', 'staging', 'production', 'console'
  if (rawRole === 'master') return `${zone}:master`
  if (rawRole === 'slave')  return `${zone}:slave`
  // Two-part format: only master/slave are valid type suffixes for icon selection.
  // Anything else (e.g. dev:erpnext) normalises to zone:unspecified.
  if (rawRole.includes(':')) {
    const type = rawRole.split(':')[1]
    if (type !== 'master' && type !== 'slave') return `${zone}:unspecified`
  }
  return rawRole
}

function nextDevPosition(cy) {
  const devNodes = cy.nodes('[zone_id = "zone-dev"]:not(.phantom)')
  const occupied = new Set(devNodes.map(n => `${Math.round(n.position('x'))},${Math.round(n.position('y'))}`))
  let slot = 0
  while (slot < 100) {
    const col = slot % 2
    const row = Math.floor(slot / 2)
    const x = Math.round(540 + col * 160)
    const y = Math.round(150 + row * 160)
    if (!occupied.has(`${x},${y}`)) return { x, y }
    slot++
  }
  return { x: 540, y: 150 + Math.floor(devNodes.length / 2) * 160 }
}

function nextPositionForZone(cy, zoneId) {
  if (zoneId === 'zone-dev') return nextDevPosition(cy)
  const base     = ZONE_BASE_POS[zoneId] ?? { baseX: 500, baseY: 650 }
  const existing = cy.nodes(`[zone_id = "${zoneId}"]:not(.phantom)`)
  const xs       = existing.map(n => n.position('x'))
  const maxX     = xs.length ? Math.max(...xs) : base.baseX - 160
  return { x: maxX + 160, y: base.baseY }
}

// Count master/slave nodes in the given zone using the two-part vm_role format.
function countZoneRoles(cy, zoneId) {
  if (!cy) return { masters: 0, slaves: 0 }
  const prefix = zoneId.replace('zone-', '')  // 'staging', 'production'
  return {
    masters: cy.nodes(`[zone_id = "${zoneId}"][vm_role = "${prefix}:master"]:not(.phantom)`).length,
    slaves:  cy.nodes(`[zone_id = "${zoneId}"][vm_role = "${prefix}:slave"]:not(.phantom)`).length,
  }
}

// ── Fallback topology (when API unreachable) ──────────────────────────────────

const FALLBACK_HOSTS = [
  { id: 'saconsole', hostname: 'saconsole', wg_role: 'hub',   wg_ip: '10.10.0.1', virbr0_ip: '192.168.122.10', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'development', 'lab'],            vm_role: 'dev:unspecified' },
  { id: 'target1',   hostname: 'target1',   wg_role: 'spoke', wg_ip: '10.10.0.3', virbr0_ip: '192.168.122.11', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'targets', 'development', 'lab'], vm_role: 'dev:unspecified' },
  { id: 'target2',   hostname: 'target2',   wg_role: 'spoke', wg_ip: '10.10.0.4', virbr0_ip: '192.168.122.12', backend: 'kvm', provisioned: true,  ansible_groups: ['kvm', 'targets', 'development', 'lab'], vm_role: 'dev:unspecified' },
]

const CONTROLLER_HOST = {
  id: 'controller', hostname: 'controller', wg_role: 'controller',
  wg_ip: '10.10.0.2', virbr0_ip: '', backend: 'local',
  provisioned: true, ansible_groups: [], vm_role: 'dev:unspecified',
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
    position: INITIAL_POSITIONS[tpl.id] ? { ...INITIAL_POSITIONS[tpl.id] } : undefined,
  }))

  const vmNodes = allHosts.map(h => {
    const zone = h.wg_role === 'controller' ? 'zone-console' : zoneFor(h)
    const vmState = h.vm_state ?? null
    const shutOff = vmState === 'shut off'
    let label = h.hostname
    if (h.provisioned === false)  label = `${h.hostname}\n[unprovisioned]`
    else if (h.provisioned === null) label = `${h.hostname}\n[unknown]`
    else if (shutOff)             label = `${h.hostname}\n[shut off]`
    return {
      data: {
        id:             h.id ?? h.hostname,
        label,
        role:           h.wg_role,
        vm_role:        normalizeVmRole(h.vm_role, zone),
        platform:       h.backend ?? 'kvm',
        wg_ip:          h.wg_ip      ?? '',
        virbr0_ip:      h.virbr0_ip  ?? '',
        provisioned:    !!h.provisioned,
        vm_state:       vmState,
        ansible_groups: h.ansible_groups ?? [],
        zone_id:        zone,
        nickname:       h.nickname   ?? '',
        erp_user:       h.erp_user   ?? '',
        erp_url:        h.erp_url    ?? '',
        hypervisor:     h.hypervisor ?? '',
      },
      position: INITIAL_POSITIONS[h.id ?? h.hostname] ? { ...INITIAL_POSITIONS[h.id ?? h.hostname] } : undefined,
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

  // ── Icons by vm_role type (zone:type format) ──
  {
    selector: 'node[vm_role = "dev:unspecified"]:not(.template-node)',
    style: { 'background-image': ICON_DEV, 'background-fit': 'contain' }
  },
  {
    // master: any zone prefix (*:master)
    selector: 'node[vm_role = "dev:master"], node[vm_role = "staging:master"], node[vm_role = "production:master"]',
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
    // slave: any zone prefix (*:slave)
    selector: 'node[vm_role = "dev:slave"], node[vm_role = "staging:slave"], node[vm_role = "production:slave"]',
    style: {
      'background-image': ICON_SLAVE,
      'background-fit':   'contain',
      'border-color':     '#66bb99',
      'border-width':     2,
      'width':            80,
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
    style: { 'border-color': '#f0a020', 'border-width': 2, 'border-style': 'dashed', 'color': '#e8c060' }
  },

  // ── Shut off (provisioned but not running) ──
  // Only matches provisioned nodes — unprovisioned keeps its amber dashed style.
  // No whole-node opacity: dim the icon only, keep label legible.
  {
    selector: 'node[vm_state = "shut off"][?provisioned]:not(.template-node):not(.phantom)',
    style: {
      'border-color':       '#556677',
      'border-style':       'dotted',
      'background-opacity': 0.15,
      'color':              '#8899aa',
    }
  },

  // ── Template lifecycle states — MUST come after VM styles ──
  // Cytoscape :not(.template-node) is buggy and matches template nodes too.
  // Placing tpl-* styles after VM styles ensures they win by array position.
  {
    selector: 'node.template-node.tpl-none',
    style: { 'opacity': 0, 'events': 'no' }
  },
  {
    selector: 'node.template-node.tpl-building',
    style: { 'border-style': 'dashed', 'border-color': '#cc8833', 'border-width': 2, 'opacity': 0.8 }
  },
  {
    selector: 'node.template-node.tpl-ready',
    style: { 'border-style': 'solid', 'border-color': '#33dd77', 'border-width': 3, 'opacity': 1, 'color': '#55ee99' }
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
      positions: node => {
        const p = INITIAL_POSITIONS[node.id()]
        return p ? { x: p.x, y: p.y } : undefined
      },
    },
  })

  // Apply CSS classes — class selectors are reliable; [attr] existence selectors
  // have a bug in Cytoscape 3.33.x where boolean/truthy values don't match.
  ZONE_ANCHORS.forEach(a      => cy.$('#' + a.id).addClass('phantom'))
  STOCKROOM_TEMPLATES.forEach(t => cy.$('#' + t.id).addClass('template-node'))

  // ERPNext tile starts invisible; _syncTemplateState fetches actual state.
  // _reconnectActiveJob must run AFTER _syncTemplateState to win the race —
  // if sync returns last it would reset tpl-building back to tpl-none.
  cy.$('#tpl-erpnext').addClass('tpl-none')
  await _syncTemplateState()

  _repositionUnknownNodes()  // place API-loaded nodes not in INITIAL_POSITIONS
  attachHandlers()
  // Hub (saconsole) and controller are water-troughs — permanently fixed in Console.
  cy.nodes('[role = "hub"], [role = "controller"]').lock()
  _updatePromoteButton()
  _reconnectActiveJob()

  // Register overlay updater, then fit in the next animation frame so the
  // flex container has its final pixel dimensions before zoom is computed.
  cy.on('pan zoom resize', _updateZoneOverlay)
  requestAnimationFrame(() => {
    _fitZoneGraph()
    _updateZoneOverlay()
  })

  // Poll VM state every 30s so icons stay honest.
  setInterval(_refreshVmState, 30_000)
}

async function _refreshVmState() {
  try {
    const data = await fetchHosts()
    for (const h of data.hosts) {
      const node = cy.$(`#${h.id ?? h.hostname}`)
      if (node.empty()) continue
      const prev = node.data('vm_state')
      const next = h.vm_state ?? null
      if (prev === next) continue

      node.data('vm_state', next)

      // Rebuild label to reflect new state
      const hostname = h.hostname ?? h.id
      const provisioned = h.provisioned
      let label = hostname
      if (provisioned === false)       label = `${hostname}\n[unprovisioned]`
      else if (provisioned === null)   label = `${hostname}\n[unknown]`
      else if (next === 'shut off')    label = `${hostname}\n[shut off]`
      node.data('label', label)
      node.data('provisioned', !!provisioned)
    }
  } catch {
    // API unreachable — leave current state unchanged
  }
}

// ── Quad-zone splitter ────────────────────────────────────────────────────────
// A draggable "+" handle at the intersection of the 4 quadrants.
// Dragging it resizes the quadrants by moving the phantom anchor nodes.

// Console quadrant minimum: the splitter can only move right/down (making Console
// larger). Initial values are the floor — Console cannot shrink below this size.
const CONSOLE_MIN_SPLIT_X = 425
const CONSOLE_MIN_SPLIT_Y = 425
let splitX = CONSOLE_MIN_SPLIT_X
let splitY = CONSOLE_MIN_SPLIT_Y

function _updateQuadAnchors(rawX, rawY) {
  // Clamp so each zone keeps at least 80 graph units of usable width/height.
  // Writes back to module-level splitX/splitY so _updateZoneOverlay reads
  // the same clamped values.
  const { LEFT, RIGHT, TOP, BOTTOM } = ZONE_GRAPH
  splitX = Math.max(CONSOLE_MIN_SPLIT_X, Math.min(RIGHT  - 80, rawX))
  splitY = Math.max(CONSOLE_MIN_SPLIT_Y, Math.min(BOTTOM - 80, rawY))

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

// Position any VM nodes that have no entry in INITIAL_POSITIONS (e.g. hosts added
// via the API after the static map was written). Without this they land at graph (0,0),
// which is outside all zone panels.
function _repositionUnknownNodes() {
  if (!cy) return
  const fallbackCount = {}
  cy.nodes().not('.phantom').not('.template-node').forEach(node => {
    if (INITIAL_POSITIONS[node.id()]) return
    const zoneId = node.data('zone_id') ?? 'zone-dev'
    if (!fallbackCount[zoneId]) fallbackCount[zoneId] = 0
    const idx = fallbackCount[zoneId]++
    let pos
    if      (zoneId === 'zone-staging')    pos = { x: ZONE_BASE_POS['zone-staging'].baseX    + idx * 160, y: ZONE_BASE_POS['zone-staging'].baseY    }
    else if (zoneId === 'zone-production') pos = { x: ZONE_BASE_POS['zone-production'].baseX + idx * 160, y: ZONE_BASE_POS['zone-production'].baseY }
    else { const col = idx % 2; const row = Math.floor(idx / 2); pos = { x: 540 + col * 160, y: 150 + row * 160 } }  // dev: 2-col grid
    node.position(pos)
  })
}

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

// Fit the viewport to the full zone graph area using ZONE_GRAPH constants.
// Unlike cy.fit(collection), this does not depend on phantom node positions
// being correct, and must be called after the cy container has been sized
// (use requestAnimationFrame to ensure flex layout has settled).
function _fitZoneGraph() {
  if (!cy) return
  const { LEFT, RIGHT, TOP, BOTTOM } = ZONE_GRAPH
  const W = cy.width(), H = cy.height()
  if (!W || !H) return
  const pad = 40
  const zoom = Math.min(
    (W - 2 * pad) / (RIGHT - LEFT),
    (H - 2 * pad) / (BOTTOM - TOP)
  )
  cy.viewport({
    zoom,
    pan: {
      x: W / 2 - (LEFT + RIGHT) / 2 * zoom,
      y: H / 2 - (TOP  + BOTTOM) / 2 * zoom,
    }
  })
}

// Stockroom bounding box in graph coordinates (surrounds the 3 template tiles — left of Console)
const STOCKROOM_GRAPH = { x1: 100, y1: 155, x2: 225, y2: 295 }

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

// Convert a camelCase or snake_case key to Title Case words.
function toTitleCase(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, c => c.toUpperCase())
}

// Render a faintly-framed multi-column specs table.
// Fields are arranged to fill columns left→right so rows are minimised.
function renderInfo(data) {
  const zone  = (data.zone_id ?? '').replace('zone-', '')
  const zoneLabel = zone ? zone.charAt(0).toUpperCase() + zone.slice(1) : ''

  // Ordered field definitions: [label, value | null to skip]
  const fields = [
    ['Hostname',   data.label?.split('\n')[0] ?? data.id],
    data.nickname ? ['Nickname',  data.nickname] : null,
    data.erp_user ? ['ERP User',  data.erp_user] : null,
    zoneLabel     ? ['Zone',      zoneLabel]      : null,
    data.wg_ip    ? ['WG IP',     data.wg_ip]     : null,
    data.virbr0_ip ? ['virbr0 IP', data.virbr0_ip] : null,
    data.hypervisor ? ['Hypervisor', data.hypervisor] : null,
  ].filter(Boolean)

  // Build grid cells: pairs of (label, value) filling 2 columns per visual row
  const cells = fields.map(([label, value]) =>
    `<span class="spec-label">${label}</span><span class="spec-value">${value}</span>`
  ).join('')

  const urlRow = data.erp_url
    ? `<div class="spec-url-row">
         <span class="spec-label">Site URL</span>
         <a class="spec-url" href="${data.erp_url}" target="_blank" rel="noopener">${data.erp_url}</a>
       </div>`
    : ''

  infoPanel.innerHTML =
    `<div class="spec-table">${cells}</div>${urlRow}`
}

// Render info + contextual action buttons for this VM node.
// No-ops while a job is running (don't overwrite the job log).
// Template tiles have their own renderTemplateInfo — bail out if called for one.
function renderInfoWithActions(data) {
  if (activeJob) return
  if (data.template === 'yes') { renderTemplateInfo(data); return }
  renderInfo(data)

  const role        = data.role
  const provisioned = data.provisioned
  const vm_role     = data.vm_role ?? 'dev:unspecified'
  const isOperational = role !== 'controller' && role !== 'hub'

  // ── Role selector — shown only for user VMs in the dev zone ──
  if (isOperational && data.zone_id === 'zone-dev') {
    const roleDiv = document.createElement('div')
    roleDiv.className = 'role-selector'
    const opts = [
      { value: 'dev:unspecified', label: 'Unspecified' },
      { value: 'dev:master',      label: 'Master'       },
      { value: 'dev:slave',       label: 'Slave'        },
    ]
    roleDiv.innerHTML = '<span class="role-label">Intended role:</span>' +
      opts.map(o =>
        `<label><input type="radio" name="vm-role-${data.id}" value="${o.value}"` +
        (vm_role === o.value ? ' checked' : '') + `> ${o.label}</label>`
      ).join('')
    roleDiv.querySelectorAll('input[type="radio"]').forEach(input => {
      input.addEventListener('change', () => {
        const node = cy.$('#' + data.id)
        node.data('vm_role', input.value)
        // Re-render info panel so Clone button state reflects the new role
        renderInfoWithActions(node.data())
      })
    })
    infoPanel.appendChild(roleDiv)
  }

  const actions = document.createElement('div')
  actions.className = 'action-bar'

  // saconsole (hub) is the machine that runs build.sh — it creates templates
  if (role === 'hub') {
    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--secondary'
    btn.textContent = 'Create Template'
    btn.onclick     = () => _startBuildTemplate('create')
    actions.appendChild(btn)
  }

  if (isOperational && !provisioned) {
    const btn = document.createElement('button')
    btn.className   = 'action-btn'
    btn.textContent = 'Provision'
    btn.onclick     = () => runProvision(data.id)
    actions.appendChild(btn)
  }

  // Refresh — idempotent re-run of differentiate.sh; only if a saved script exists
  if (isOperational && provisioned && data.erp_url) {
    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--secondary'
    btn.textContent = 'Refresh ↺'
    btn.title       = 'Re-run differentiation script (idempotent)'
    btn.onclick     = () => runRefresh(data.id)
    actions.appendChild(btn)
  }

  // ── VM power control: Start / Stop / Reboot ──
  if (isOperational && provisioned) {
    const vmState = data.vm_state ?? null
    if (vmState === 'shut off') {
      const btn = document.createElement('button')
      btn.className   = 'action-btn action-btn--start'
      btn.textContent = '▶ Start'
      btn.title       = 'Start this VM (memory check will run first)'
      btn.onclick     = () => _vmPowerAction(data.id, 'start')
      actions.appendChild(btn)
    }
    if (vmState === 'running') {
      const stopBtn = document.createElement('button')
      stopBtn.className   = 'action-btn action-btn--stop'
      stopBtn.textContent = '⏹ Stop'
      stopBtn.title       = 'Graceful shutdown (virsh shutdown)'
      stopBtn.onclick     = () => _vmPowerAction(data.id, 'stop')
      actions.appendChild(stopBtn)

      const rebootBtn = document.createElement('button')
      rebootBtn.className   = 'action-btn action-btn--secondary'
      rebootBtn.textContent = '↻ Reboot'
      rebootBtn.title       = 'Reboot this VM'
      rebootBtn.onclick     = () => _vmPowerAction(data.id, 'reboot')
      actions.appendChild(rebootBtn)
    }
  }

  // Clone to Staging — provisioned dev spoke; disabled if role unsuitable
  if (isOperational && provisioned && data.zone_id === 'zone-dev') {
    const roleType = vm_role.split(':')[1]  // 'unspecified', 'master', 'slave'
    const { masters: stgMasters, slaves: stgSlaves } = countZoneRoles(cy, 'zone-staging')
    const canClone  = roleType !== 'unspecified'
                   && !(roleType === 'master' && stgMasters >= 1)
                   && !(roleType === 'slave'  && stgSlaves  >= 1)
    const cloneHint = !canClone
      ? (roleType === 'unspecified'
          ? 'Declare a role (Master or Slave) before cloning to Staging'
          : `Staging already has a ${roleType}. Remove it first.`)
      : 'Deploy a new VM in Staging (fresh provision — not a disk copy)'

    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--clone'
    btn.textContent = 'Clone to Staging'
    btn.disabled    = !canClone
    btn.title       = cloneHint
    btn.onclick     = () => openDialogForZone('staging', data.id, data.vm_role)
    actions.appendChild(btn)
  }

  if (isOperational) {
    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--danger'
    btn.textContent = provisioned ? 'Destroy VM' : 'Remove'
    btn.onclick     = () => runDestroy(data.id, provisioned)
    actions.appendChild(btn)
  }

  if (provisioned && (role === 'hub' || (isOperational && data.erp_url))) {
    const btn = document.createElement('button')
    btn.className   = 'action-btn action-btn--inspect'
    btn.textContent = 'Inspect ›'
    btn.onclick     = () => openPopup(data.id)
    actions.appendChild(btn)
  }

  if (actions.childElementCount) infoPanel.appendChild(actions)
}

// Render info + Deploy button for a Stockroom template tile
async function renderTemplateInfo(data) {
  const title = data.label.replace('\n', ' — ')
  infoPanel.innerHTML =
    `<p class="hint"><strong>${title}</strong></p>` +
    `<p class="hint" style="margin-top:6px">Click <em>Deploy from Template</em> to add a VM pre-configured for this role.</p>`

  // ERPNext tile: show current template version + date
  if (data.id === 'tpl-erpnext') {
    const statusEl = document.createElement('p')
    statusEl.className = 'hint'
    statusEl.style.marginTop = '6px'
    statusEl.textContent = 'Checking template status…'
    infoPanel.appendChild(statusEl)
    try {
      const s = await fetchTemplateStatus()
      if (s.image) {
        const d = s.built_at ? new Date(s.built_at).toLocaleDateString() : 'unknown date'
        statusEl.innerHTML =
          `<span style="color:#8f8">✓ ${s.image}</span><br>` +
          `<small style="color:#aaa">Built: ${d} · ${s.frappe_branch ?? ''}</small>`
      } else {
        statusEl.innerHTML = '<span style="color:#fa8">⚠ No template built yet</span>'
      }
    } catch {
      statusEl.textContent = 'Template status unavailable'
    }
  }

  const actions = document.createElement('div')
  actions.className = 'action-bar'

  const deployBtn = document.createElement('button')
  deployBtn.className   = 'action-btn'
  deployBtn.textContent = 'Create VM'
  deployBtn.onclick     = () => openDialogFromTemplate(data)
  actions.appendChild(deployBtn)

  // ERPNext tile only: update + destroy buttons
  if (data.id === 'tpl-erpnext') {
    const buildBtn = document.createElement('button')
    buildBtn.className   = 'action-btn action-btn--secondary'
    buildBtn.textContent = 'Update Template'
    buildBtn.onclick     = () => _startBuildTemplate()
    actions.appendChild(buildBtn)

    // Destroy Template — only shown when an artifact exists on toshiba
    const _addDestroyBtn = (hasArtifact) => {
      if (!hasArtifact) return
      const destroyBtn = document.createElement('button')
      destroyBtn.className   = 'action-btn action-btn--danger'
      destroyBtn.textContent = 'Destroy Template'
      destroyBtn.onclick     = () => _destroyTemplate()
      actions.appendChild(destroyBtn)
    }
    // status already fetched above — reuse via closure if available, else re-fetch
    fetchTemplateStatus()
      .then(s => _addDestroyBtn(!!s.image))
      .catch(() => {})
  }

  infoPanel.appendChild(actions)
}

// ── Template tile lifecycle state ─────────────────────────────────────────────

function _setTemplateState(state) {
  const node = cy.$('#tpl-erpnext')
  if (!node.length) return
  node.removeClass('tpl-none tpl-building tpl-ready')
  node.addClass(`tpl-${state}`)
  cy.style().update()
}

async function _syncTemplateState() {
  try {
    const s = await fetchTemplateStatus()
    _setTemplateState(s.image ? 'ready' : 'none')
  } catch {
    _setTemplateState('none')
  }
}

// Inline confirm → build template job
// mode: 'create' (from saconsole) | 'update' (from template tile)
function _startBuildTemplate(mode = 'update') {
  if (activeJob) return

  const isCreate   = mode === 'create'
  const title      = isCreate ? 'Create ERPNext v13 Template' : 'Update ERPNext v13 Template'
  const bodyCopy   = isCreate
    ? 'Runs a ~45 min Packer build on saconsole.<br>Produces the undifferentiated base image: OS + MariaDB + bench + frappe + erpnext. No site. No apps. No data.'
    : 'Runs a ~45 min Packer build on saconsole.<br>Replaces the current base image for all future ERPNext deployments.'
  const confirmTxt = isCreate ? 'Confirm Create' : 'Confirm Update'
  const cancelMsg  = isCreate ? 'Create cancelled.' : 'Update cancelled.'

  infoPanel.innerHTML =
    `<p class="hint"><strong>${title}</strong></p>` +
    `<p class="hint" style="color:#fa8;margin-top:6px">${bodyCopy}</p>`

  const actions = document.createElement('div')
  actions.className = 'action-bar'

  const confirmBtn = document.createElement('button')
  confirmBtn.className   = 'action-btn'
  confirmBtn.textContent = confirmTxt
  confirmBtn.onclick = () => {
    infoPanel.innerHTML = '<pre class="job-log">Starting ERPNext template build on saconsole…\n</pre>'
    startBuildTemplate()
      .then(({ job_id }) => {
        _setTemplateState('building')
        localStorage.setItem(JOB_KEY, JSON.stringify({ job_id, hostname: 'template', type: 'build_template' }))
        _attachJobPoller(job_id, 'template', 'build_template')
      })
      .catch(err => {
        infoPanel.innerHTML = `<p class="hint error">Build failed to start: ${err.message}</p>`
      })
  }

  const cancelBtn = document.createElement('button')
  cancelBtn.className   = 'action-btn action-btn--secondary'
  cancelBtn.textContent = 'Cancel'
  cancelBtn.onclick     = () => hint(cancelMsg)
  actions.appendChild(confirmBtn)
  actions.appendChild(cancelBtn)
  infoPanel.appendChild(actions)
}

// ── ANSI → HTML converter ──────────────────────────────────────────────────

const _ANSI_COLORS = {
  '30': '#666', '1;30': '#888',
  '31': '#e57373', '1;31': '#f44336', '0;31': '#e57373',
  '32': '#81c784', '1;32': '#4caf50', '0;32': '#81c784',
  '33': '#ffb74d', '1;33': '#ff9800', '0;33': '#ffb74d',
  '34': '#64b5f6', '1;34': '#42a5f5',
  '35': '#ba68c8', '1;35': '#9c27b0',
  '36': '#4dd0e1', '1;36': '#00bcd4',
  '37': '#e0e0e0', '1;37': '#ffffff',
}

function _ansiToHtml(raw) {
  // Escape HTML entities first
  let s = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Strip cursor-movement / erase sequences (e.g. \x1b[1A \x1b[2K \x1b[K)
  s = s.replace(/\x1b\[[0-9;]*[A-HJKST]/g, '')

  // Convert SGR color sequences to <span>
  let openSpans = 0
  s = s.replace(/\x1b\[([0-9;]*)m/g, (_, code) => {
    if (code === '' || code === '0') {
      const closes = '</span>'.repeat(openSpans)
      openSpans = 0
      return closes
    }
    const color = _ANSI_COLORS[code]
    if (color) { openSpans++; return `<span style="color:${color}">` }
    return ''
  })
  s += '</span>'.repeat(openSpans)
  return s
}

function _colorLine(raw) {
  const html = _ansiToHtml(raw)
  // Progress bar lines (Packer download/extract)
  if (raw.includes('━') || raw.includes('⠿') || raw.match(/^\s*[\d.]+ [KMG]iB/)) {
    return `<span class="log-progress">${html}</span>`
  }
  // Section headers ("── Phase N: ...")
  if (raw.match(/^──\s/) || raw.match(/^==/)) {
    return `<span class="log-section">${html}</span>`
  }
  // Build complete / done lines
  if (raw.match(/Build complete|image ready|✓.*complete|Done —/i)) {
    return `<span class="log-done">${html}</span>`
  }
  // pkg_resources deprecation — upstream noise from frappe/supervisor, not a real error
  if (raw.includes('pkg_resources')) {
    return `<span class="log-warn">${html}</span>\n<span class="log-ignore"><strong>↑ ignore — upstream Python deprecation warning</strong></span>`
  }
  // Error-bearing lines (not inside ANSI span — catch plain ones too)
  if (raw.match(/\bERROR\b|\bFAILED\b/i) && !raw.match(/\x1b\[/)) {
    return `<span class="log-error-line">${html}</span>`
  }
  return html
}

function renderJobLog(lines, done, status) {
  let pre = infoPanel.querySelector('pre.job-log')
  if (!pre) {
    infoPanel.innerHTML = ''
    pre = document.createElement('pre')
    pre.className = 'job-log'
    infoPanel.appendChild(pre)
  }
  if (lines.length) {
    const frag = document.createDocumentFragment()
    const span = document.createElement('span')
    span.innerHTML = lines.map(_colorLine).join('\n') + '\n'
    frag.appendChild(span)
    pre.appendChild(frag)
  }
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

// Destroy the built artifact on toshiba (reset to "not_built" state)
function _destroyTemplate() {
  if (activeJob) return
  infoPanel.innerHTML =
    '<p class="hint"><strong>Destroy ERPNext v13 Template</strong></p>' +
    '<p class="hint" style="color:#f88;margin-top:6px">' +
    'Deletes the qcow2 image and metadata from toshiba.<br>' +
    'Any new deployment will require a fresh build.' +
    '</p>'
  const actions = document.createElement('div')
  actions.className = 'action-bar'
  const confirmBtn = document.createElement('button')
  confirmBtn.className   = 'action-btn action-btn--danger'
  confirmBtn.textContent = 'Confirm Destroy'
  confirmBtn.onclick = () => {
    deleteTemplate()
      .then(() => hint('Template artifact deleted. Run "Create Template" from saconsole to rebuild.'))
      .catch(err => { infoPanel.innerHTML = `<p class="hint error">Destroy failed: ${err.message}</p>` })
  }
  const cancelBtn = document.createElement('button')
  cancelBtn.className   = 'action-btn action-btn--secondary'
  cancelBtn.textContent = 'Cancel'
  cancelBtn.onclick     = () => hint('Destroy cancelled.')
  actions.appendChild(confirmBtn)
  actions.appendChild(cancelBtn)
  infoPanel.appendChild(actions)
}

// ── Provision flow ────────────────────────────────────────────────────────────

const JOB_KEY  = 'esacp_active_job'
let   activeJob = null  // { job_id, hostname, type } — set while a job is in progress

function runRefresh(hostname) {
  infoPanel.innerHTML = `<pre class="job-log">Starting refresh for ${hostname}...\n</pre>`
  startRefresh(hostname)
    .then(({ job_id }) => {
      localStorage.setItem(JOB_KEY, JSON.stringify({ job_id, hostname, type: 'refresh' }))
      _attachJobPoller(job_id, hostname, 'refresh')
    })
    .catch(err => {
      infoPanel.innerHTML = `<p class="hint error">Refresh failed to start: ${err.message}</p>`
    })
}

// ── VM power control (start / stop / reboot) ────────────────────────────────

async function _vmPowerAction(hostname, action) {
  const labels = { start: 'Starting', stop: 'Stopping', reboot: 'Rebooting' }
  const apiFn  = { start: startVm,    stop: stopVm,     reboot: rebootVm }
  infoPanel.innerHTML = `<p class="hint">${labels[action]} ${hostname}...</p>`
  try {
    const result = await apiFn[action](hostname)
    infoPanel.innerHTML = `<p class="hint">${result.message}</p>`
    // Immediate state refresh — don't wait for the 30s poll
    await _refreshVmState()
    // Re-render info panel with updated buttons
    const node = cy.$(`#${hostname}`)
    if (!node.empty()) renderInfoWithActions(node.data())
  } catch (err) {
    infoPanel.innerHTML = `<p class="hint error">${err.message}</p>`
  }
}

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
      if (type === 'build_template') {
        _setTemplateState(status === 'done' ? 'ready' : 'none')
      } else if (status === 'done') {
        if (type === 'provision' || type === 'provision_erpnext') {
          const node = cy.$(`#${hostname}`)
          node.data('provisioned', true)
          node.data('label', hostname)
        } else if (type === 'destroy') {
          const node = cy.$(`#${hostname}`)
          cy.remove(node.connectedEdges())
          cy.remove(node)
          hint('Click an ERPNext template tile to add a VM.')
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
    if (type === 'build_template') _setTemplateState('building')
    _attachJobPoller(job_id, hostname, type ?? 'provision')
  } catch {
    localStorage.removeItem(JOB_KEY)
  }
}

// ── Event handlers ────────────────────────────────────────────────────────────

function attachHandlers() {
  // All node clicks — renderInfoWithActions guards for templates internally
  cy.on('tap', 'node:not(.phantom)', evt => {
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
      hint('Click a node or edge to inspect it. Click an ERPNext template tile to add a VM.')
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

  // ── Template tile drag-to-deploy ──
  // The tile is a factory — it always snaps back. Dropping it in a zone opens the Add dialog.
  cy.on('grab', 'node.template-node.tpl-ready', evt => {
    _preDragPos.set(evt.target.id(), { ...evt.target.position() })
  })

  cy.on('dragfree', 'node.template-node.tpl-ready', evt => {
    const node   = evt.target
    const dropZoneId = _zoneAtPos(node.position())

    const home = INITIAL_POSITIONS[node.id()] ?? { x: 160, y: 220 }

    // Open Add dialog only if dropped in Dev (Staging/Production require Promote workflow).
    // Tile stays at drop position while dialog is open; snaps back on dialog close.
    if (dropZoneId === 'zone-dev') {
      openDialogFromTemplate({ ...node.data(), targetZone: 'development' })
    } else if (dropZoneId && dropZoneId !== 'zone-console') {
      // Dropped in wrong zone — snap back immediately and show hint
      setTimeout(() => node.position(home), 50)
      setStatus('Drag the ERPNext tile into the Development zone to deploy a new VM.')
    } else {
      // Dropped in Console or outside — snap back
      setTimeout(() => node.position(home), 50)
    }
  })

  // Record position before drag begins (needed for snap-back on rejected drops)
  // Guard: Cytoscape :not(.template-node) is buggy — check class explicitly.
  cy.on('grab', 'node:not(.phantom):not(.template-node)', evt => {
    const n = evt.target
    if (n.hasClass('template-node') || n.hasClass('phantom')) return
    _preDragPos.set(n.id(), { ...n.position() })
  })

  // On drop: detect which zone the node landed in; reassign or reject
  // Guard: Cytoscape :not(.template-node) is buggy — check class explicitly.
  cy.on('dragfree', 'node:not(.phantom):not(.template-node)', evt => {
    const node = evt.target
    if (node.hasClass('template-node') || node.hasClass('phantom')) return
    const role = node.data('role')

    const pos       = node.position()
    const newZoneId = _zoneAtPos(pos)
    const oldZoneId = node.data('zone_id')

    function snapBack() {
      const prev = _preDragPos.get(node.id())
      if (prev) node.position(prev)
      _preDragPos.delete(node.id())
    }

    // Hub and controller are locked — cannot be dragged (kept as safety guard)
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

    // ── Crossed into staging ──────────────────────────────────────────────────
    // vm_role must be declared (dev:master or dev:slave) before crossing the fence.
    // The declared type determines which slot is taken in staging.
    if (newZoneId === 'zone-staging') {
      if (!node.data('provisioned')) {
        hint('Only provisioned VMs can be assigned to Staging. Provision this VM first.')
        snapBack()
        return
      }

      const currentRole = node.data('vm_role')  // two-part: 'dev:master' etc.
      const roleType    = currentRole?.split(':')[1]  // 'unspecified', 'master', 'slave'

      if (!roleType || roleType === 'unspecified') {
        hint('Declare a role (Master or Slave) before moving to Staging.')
        snapBack()
        return
      }

      const { masters: existingMasters, slaves: existingSlaves } = countZoneRoles(cy, 'zone-staging')
      if (roleType === 'master' && existingMasters >= 1) {
        hint('Staging already has a Master. Remove it first or declare Slave.')
        snapBack()
        return
      }
      if (roleType === 'slave' && existingSlaves >= 1) {
        hint('Staging already has a Slave. Remove it first or declare Master.')
        snapBack()
        return
      }

      node.data('zone_id', 'zone-staging')
      node.data('vm_role', `staging:${roleType}`)
      _preDragPos.delete(node.id())
      _updatePromoteButton()
      return
    }

    // ── Crossed back into dev ─────────────────────────────────────────────────
    // Keep the declared role type (master/slave) so user can drag back easily.
    // 'staging:master' → 'dev:master', slot freed in staging.
    const currentRole = node.data('vm_role')
    const roleType    = currentRole?.split(':')[1] ?? 'unspecified'
    node.data('zone_id', 'zone-dev')
    node.data('vm_role', `dev:${roleType}`)
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

// #btn-add-target removed from header — Add Target triggered from template tile only


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
const dialogTitle   = document.getElementById('dialog-title')

// Set when dialog is opened from a template tile drag; cleared on close.
// Passed to addHost so the backend knows to use vol-clone + --import instead of ISO.
let _dialogTemplateId = null

const ZONE_DOMAINS = { development: 'iridium.blue', staging: 'iridium.blue', production: 'logichem.solutions' }
const siteUrlPreview  = document.getElementById('site-url-preview')
const fieldSiteUrl    = document.getElementById('field-site-url-preview')
const fNicknameHint   = document.getElementById('f-nickname-hint')

function _updateSiteUrlPreview() {
  if (!_dialogTemplateId) return
  const h = fHostname.value.trim()
  const domain = ZONE_DOMAINS[fZone.value] ?? 'iridium.blue'
  siteUrlPreview.textContent = h ? `https://${h}.${domain}` : ''
}
fHostname.addEventListener('input', _updateSiteUrlPreview)
fZone.addEventListener('change', _updateSiteUrlPreview)

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
  _dialogTemplateId = opts.templateId ?? null
  const isTemplate = !!_dialogTemplateId
  if (dialogTitle) {
    dialogTitle.textContent = isTemplate ? 'Deploy from Template' : 'Add Target'
  }
  fHostname.value   = opts.hostname   ?? ''
  fNickname.value   = ''
  fNickname.required = isTemplate
  if (fNicknameHint) fNicknameHint.style.display = isTemplate ? '' : 'none'
  if (fieldSiteUrl) fieldSiteUrl.style.display = isTemplate ? '' : 'none'
  fWgIp.value       = apiSuggestions.wg_ip
  fVirbr0Ip.value   = apiSuggestions.virbr0_ip
  fBackend.value    = 'kvm'
  fHypervisor.value = apiSuggestions.hypervisor ?? 'toshiba'
  fZone.value       = opts.zone    ?? 'development'
  fVmRole.value     = opts.vm_role ?? 'dev'
  dialogError.classList.add('hidden')
  dialogError.textContent = ''
  submitBtn.disabled    = false
  submitBtn.textContent = isTemplate ? 'Deploy' : 'Add'
  _refreshRoleOptions()
  _updateSiteUrlPreview()
  dialogOverlay.classList.remove('hidden')
  fHostname.focus()
}

function closeDialog() {
  // Snap template tile back to Stockroom home if dialog was opened from a drag.
  // Always use INITIAL_POSITIONS — template tiles have a fixed home.
  if (_dialogTemplateId) {
    const tpl = cy && cy.$('#' + _dialogTemplateId)
    const home = INITIAL_POSITIONS[_dialogTemplateId]
    if (tpl && tpl.length && home) setTimeout(() => { tpl.position(home); cy.forceRender() }, 200)
  }
  _dialogTemplateId = null
  dialogOverlay.classList.add('hidden')
}

// Open dialog pre-filled from a Stockroom template tile.
// tplData.targetZone: zone from drag-drop (overrides defaultZone when present).
function openDialogFromTemplate(tplData) {
  const zone   = tplData.targetZone ?? tplData.defaultZone
  const vmRole = zone === 'development' ? 'dev' : (tplData.defaultRole ?? 'master')
  openDialog({ zone, vm_role: vmRole, templateId: tplData.id })
}

// Open dialog pre-filled for a target zone (e.g. Clone to Staging).
// sourceVmRole: the source dev node's two-part role ('dev:master' etc.) — used to
// pre-select the role in the dialog so the user doesn't have to repeat the choice.
function openDialogForZone(zone, sourceHostname, sourceVmRole) {
  const roleType = sourceVmRole?.split(':')[1]  // 'master', 'slave', or 'unspecified'
  const vm_role  = roleType && roleType !== 'unspecified' ? roleType : undefined
  openDialog({ zone, vm_role })
  if (sourceHostname) fHostname.value = `${sourceHostname}-staging`
}

document.getElementById('dialog-cancel').addEventListener('click', closeDialog)

dialogOverlay.addEventListener('click', e => {
  if (e.target === dialogOverlay) closeDialog()
})

document.getElementById('add-target-form').addEventListener('submit', async e => {
  e.preventDefault()
  dialogError.classList.add('hidden')
  submitBtn.disabled    = true
  submitBtn.textContent = _dialogTemplateId ? 'Deploying…' : 'Adding…'

  const hostname   = fHostname.value.trim()
  const nickname   = fNickname.value.trim()
  const wg_ip      = fWgIp.value.trim()
  const virbr0_ip  = fVirbr0Ip.value.trim()
  const backend    = fBackend.value
  const hypervisor = fHypervisor.value.trim()
  const zone       = fZone.value
  const vm_role    = zone === 'development' ? 'dev:unspecified' : `${zone}:${fVmRole.value}`

  try {
    if (_dialogTemplateId) {
      if (!nickname) throw new Error('Nickname is required for template deployments')
      if (!/^[A-Za-z0-9]+$/.test(nickname)) throw new Error('Nickname must be alphanumeric (no spaces or hyphens)')
      // Template-based: single atomic endpoint — registers host AND starts vol-clone job
      const { job_id } = await startProvisionErpnext({
        hostname, nickname, virbr0_ip, wg_ip, hypervisor, zone, vm_role,
      })
      // Node appears immediately (unprovisioned); tile snaps back; job runs in background
      closeDialog()
      // If node already on graph (re-provision of existing unprovisioned host), skip adding
      if (cy.$(`#${hostname}`).empty()) {
        _addNodeToGraph({ hostname, wg_ip, virbr0_ip, backend, zone, vm_role })
      }
      infoPanel.innerHTML = `<pre class="job-log">Deploying ${hostname} from template...\n</pre>`
      localStorage.setItem(JOB_KEY, JSON.stringify({ job_id, hostname, type: 'provision_erpnext' }))
      _attachJobPoller(job_id, hostname, 'provision_erpnext')
    } else {
      // Regular add: just register the host — user clicks Provision separately
      await addHost({ hostname, nickname, virbr0_ip, wg_ip, backend, hypervisor, zone, vm_role })
      closeDialog()
      _addNodeToGraph({ hostname, wg_ip, virbr0_ip, backend, zone, vm_role })
    }
    fetchHosts()
      .then(d => { apiSuggestions = d.suggestions })
      .catch(() => {})
  } catch (err) {
    dialogError.textContent = err.message
    dialogError.classList.remove('hidden')
    submitBtn.disabled    = false
    submitBtn.textContent = _dialogTemplateId ? 'Deploy' : 'Add'
  }
})

function _zoneIdFor(zone) {
  if (zone === 'staging')    return 'zone-staging'
  if (zone === 'production') return 'zone-production'
  return 'zone-dev'
}

function _addNodeToGraph({ hostname, wg_ip, virbr0_ip, backend, zone = 'development', vm_role = 'dev:unspecified' }) {
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
