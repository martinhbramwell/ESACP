// popup.js — generic drill-down popup with breadcrumb navigation
//
// Entry point: openPopup(nodeId)   e.g. openPopup('saconsole')
// Navigation:  drillTo(path)       e.g. drillTo(['saconsole', 'prometheus'])
// Each level calls registry[...].fetch() → { nodes, edges } and renders it.
// Nodes whose IDs exist as children in the registry are marked as drillable
// (double border) and navigate deeper on click.

import cytoscape from 'cytoscape'
import { registry, resolve } from './registry.js'

// ── DOM refs ───────────────────────────────────────────────────────────────

const overlay      = document.getElementById('popup-overlay')
const breadcrumbEl = document.getElementById('popup-breadcrumb')
const closeBtn     = document.getElementById('popup-close')
const popupCyEl    = document.getElementById('popup-cy')
const popupInfoEl  = document.getElementById('popup-info')
const resizeHandle = document.getElementById('popup-resize-handle')

// ── State ──────────────────────────────────────────────────────────────────

let popupCy  = null
let navStack = []   // e.g. ['saconsole'] or ['saconsole', 'prometheus']

// ── Info panel ─────────────────────────────────────────────────────────────

function renderInfo(data) {
  const rows = Object.entries(data)
    .filter(([k]) => k !== 'id')
    .map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`)
    .join('')
  popupInfoEl.innerHTML = `<table>${rows}</table>`
}

function hint(msg) {
  popupInfoEl.innerHTML = `<p class="hint">${msg}</p>`
}

// ── Breadcrumb ─────────────────────────────────────────────────────────────

function renderBreadcrumb() {
  const parts = []

  // "Lab" always navigates back to the main canvas (closes popup)
  parts.push(`<button class="bc-link" data-action="close">Lab</button>`)

  navStack.forEach((id, i) => {
    const path   = navStack.slice(0, i + 1)
    const label  = resolve(path)?.label ?? id
    const isLast = i === navStack.length - 1

    parts.push(`<span class="bc-sep">›</span>`)

    if (isLast) {
      parts.push(`<span class="bc-current">${label}</span>`)
    } else {
      parts.push(
        `<button class="bc-link" data-path='${JSON.stringify(path)}'>${label}</button>`
      )
    }
  })

  breadcrumbEl.innerHTML = parts.join('')

  breadcrumbEl.querySelector('[data-action="close"]')
    ?.addEventListener('click', hidePopup)

  breadcrumbEl.querySelectorAll('[data-path]').forEach(btn => {
    btn.addEventListener('click', () => drillTo(JSON.parse(btn.dataset.path)))
  })
}

// ── Graph renderer ─────────────────────────────────────────────────────────

function renderGraph({ nodes, edges }) {
  // Which node IDs are drillable at this level?
  const entry       = resolve(navStack)
  const drillable   = new Set(Object.keys(entry?.children ?? {}))

  const annotated = nodes.map(n => ({
    ...n,
    data: { ...n.data, drillable: drillable.has(n.data.id) ? 'yes' : 'no' },
  }))

  if (popupCy) { popupCy.destroy(); popupCy = null }

  popupCy = cytoscape({
    container: popupCyEl,
    elements:  { nodes: annotated, edges },

    style: [
      {
        selector: 'node',
        style: {
          shape:              'rectangle',
          'background-color': '#0d2137',
          'border-width':     1.5,
          'border-color':     '#2a5a9a',
          label:              'data(label)',
          color:              '#e0e0e0',
          'font-family':      'monospace',
          'font-size':        '10px',
          'text-valign':      'center',
          'text-halign':      'center',
          'text-wrap':        'wrap',
          'text-max-width':   '88px',
          width:              92,
          height:             36,
        },
      },
      {
        // Drillable nodes: double border + cursor hint
        selector: 'node[drillable = "yes"]',
        style: {
          'border-style': 'double',
          'border-width':  3,
          'border-color':  '#4fc3f7',
          cursor:          'pointer',
        },
      },
      {
        // Prometheus scrape-job nodes (larger, lighter)
        selector: 'node[type = "job"]',
        style: {
          'background-color': '#0f2a3e',
          'border-color':     '#1a6a9a',
          'font-size':        '11px',
          width:              104,
          height:             40,
        },
      },
      {
        selector: 'node[type = "instance"][health = "up"]',
        style: { 'border-color': '#4caf50' },
      },
      {
        selector: 'node[type = "instance"][health = "down"]',
        style: { 'border-color': '#f44336', 'background-color': '#2a0808' },
      },
      {
        selector: 'node:selected',
        style: { 'border-color': '#ffcc00', 'border-width': 2.5 },
      },
      {
        selector: 'edge',
        style: {
          width:                    1,
          'line-color':             '#1a3a5c',
          'target-arrow-color':     '#1a3a5c',
          'target-arrow-shape':     'triangle',
          'arrow-scale':            0.8,
          'curve-style':            'bezier',
          label:                    'data(label)',
          color:                    '#445',
          'font-family':            'monospace',
          'font-size':              '8px',
          'text-rotation':          'autorotate',
          'text-background-color':  '#1a1a2e',
          'text-background-opacity': 1,
          'text-background-padding': '2px',
        },
      },
      {
        selector: 'edge:selected',
        style: {
          'line-color':         '#ffcc00',
          'target-arrow-color': '#ffcc00',
          color:                '#ffcc00',
        },
      },
    ],

    layout: {
      name:           'cose',
      animate:        false,
      padding:        30,
      nodeRepulsion:  12000,
      idealEdgeLength: 80,
      gravity:        0.6,
    },
  })

  popupCy.on('tap', 'node', evt => {
    const data = evt.target.data()
    renderInfo(data)
    if (data.drillable === 'yes') drillTo([...navStack, data.id])
  })

  popupCy.on('tap', 'edge', evt => renderInfo(evt.target.data()))

  popupCy.on('tap', evt => {
    if (evt.target === popupCy) {
      hint('Click a node to inspect it. Double-bordered nodes drill deeper.')
    }
  })
}

// ── Service grid (ERPNext 3-box view) ──────────────────────────────────────

function tlClass(status) {
  if (status === 'green')  return 'tl--green'
  if (status === 'red')    return 'tl--red'
  if (status === 'amber')  return 'tl--amber'
  return 'tl--unknown'
}

function renderSvcGrid(nodes) {
  if (popupCy) { popupCy.destroy(); popupCy = null }

  const typeMap = { web: 'svc-box--web', app: 'svc-box--app', db: 'svc-box--db' }

  const boxes = nodes.map(n => {
    const d    = n.data
    const cls  = typeMap[d.svcType] ?? ''
    const tl   = `<span class="tl ${tlClass(d.status)}"></span>`
    return `
      <div class="svc-box ${cls}">
        <div class="svc-box-header">${tl}${d.label}</div>
        <div class="svc-box-body">
          <span class="detail-key">${d.detail1Key}:</span>
          <span class="detail-value"> ${d.detail1Val}</span><br>
          <span class="detail-key">${d.detail2Key}:</span>
          <span class="detail-value"> ${d.detail2Val}</span><br>
          <span class="detail-key">${d.detail3Key}:</span>
          <span class="detail-value"> ${d.detail3Val}</span>
        </div>
      </div>`
  }).join('')

  popupCyEl.innerHTML = `<div class="svc-grid">${boxes}</div>`
  popupInfoEl.innerHTML = '<p class="hint">Traffic lights show live service status. Click a box to see details in this panel.</p>'

  // Box click → show details below
  popupCyEl.querySelectorAll('.svc-box').forEach((el, i) => {
    el.addEventListener('click', () => {
      const d = nodes[i].data
      popupInfoEl.innerHTML = `
        <table>
          <tr><td class="spec-label">${d.detail1Key}</td><td>${d.detail1Val}</td></tr>
          <tr><td class="spec-label">${d.detail2Key}</td><td>${d.detail2Val}</td></tr>
          <tr><td class="spec-label">${d.detail3Key}</td><td>${d.detail3Val}</td></tr>
        </table>`
    })
  })
}

// ── Navigation ─────────────────────────────────────────────────────────────

async function drillTo(path) {
  const entry = resolve(path)
  if (!entry) return

  navStack = path
  renderBreadcrumb()
  hint('Loading…')

  const graph = await entry.fetch()

  if (entry.mode === 'svc') {
    renderSvcGrid(graph.nodes)
  } else {
    renderGraph(graph)
    hint('Click a node to inspect it. Double-bordered nodes drill deeper.')
  }
}

// ── Popup lifecycle ────────────────────────────────────────────────────────

export function openPopup(nodeId) {
  overlay.classList.remove('hidden')
  requestAnimationFrame(() => drillTo([nodeId]))
}

function hidePopup() {
  overlay.classList.add('hidden')
  navStack = []
  if (popupCy) { popupCy.destroy(); popupCy = null }
}

closeBtn.addEventListener('click', hidePopup)
overlay.addEventListener('click', evt => { if (evt.target === overlay) hidePopup() })
document.addEventListener('keydown', evt => { if (evt.key === 'Escape') hidePopup() })

// ── Popup resize handle ────────────────────────────────────────────────────

let resizing = false

resizeHandle.addEventListener('mousedown', e => {
  resizing = true
  resizeHandle.classList.add('dragging')
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'ns-resize'
  e.preventDefault()
})

document.addEventListener('mousemove', e => {
  if (!resizing) return

  const cyTop      = popupCyEl.getBoundingClientRect().top
  const popupBot   = document.getElementById('popup').getBoundingClientRect().bottom
  const handleH    = resizeHandle.offsetHeight

  const newCyH   = e.clientY - cyTop
  const newInfoH = popupBot - e.clientY - handleH

  if (newCyH > 60 && newInfoH > 32) {
    popupCyEl.style.flex   = 'none'
    popupCyEl.style.height = newCyH + 'px'
    popupInfoEl.style.height = newInfoH + 'px'
    popupCy?.resize()
  }
})

document.addEventListener('mouseup', () => {
  if (!resizing) return
  resizing = false
  resizeHandle.classList.remove('dragging')
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
})
