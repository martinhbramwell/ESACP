// @ts-check
import { test, expect } from '@playwright/test'
import { spawn, execSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { BASE_URL, API_URL, waitForGraph } from './helpers.js'

/**
 * Acceptance Run 01 — CLI saconsole rebuild (row 1 of the 7-run transport-parity matrix).
 *
 * Single atomic invocation of `platforms/kvm/rebuild_saconsole.sh` (no arg → `all`:
 * backup → teardown → bootstrap → verify). Observes the live Cytoscape UI and
 * asserts post-rebuild convergence.
 *
 * Plan:    ~/.claude/plans/acceptance-matrix-transport-parity.md
 * Agenda:  docs/SessionLogs/acceptance-matrix/01-cli-saconsole-rebuild.md
 * Params:  docs/SessionLogs/acceptance-matrix/params/01-cli-saconsole.yml
 *
 * saconsole lifecycle is CLI-only by design (`feedback_saconsole_cli_only.md`).
 * This run has no UI parity partner; its unique matrix contribution is
 * measured convergence timing for a hub rebuild, as a committed regression tripwire.
 */

const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)
const PROJECT_ROOT = path.resolve(__dirname, '../../..')
const PARAM_PATH = path.join(
  PROJECT_ROOT,
  'docs/SessionLogs/acceptance-matrix/params/01-cli-saconsole.yml'
)

function loadParams() {
  const raw = readFileSync(PARAM_PATH, 'utf8')
  const params = {}
  for (const line of raw.split('\n')) {
    const m = line.match(/^\s*([a-z_]+)\s*:\s*(.+?)\s*$/)
    if (!m) continue
    const [, k, v] = m
    const quoted = v.match(/^["'](.*)["']$/)
    if (quoted) { params[k] = quoted[1]; continue }
    if (/^-?\d+$/.test(v)) params[k] = parseInt(v, 10)
    else if (v === 'true' || v === 'false') params[k] = v === 'true'
    else params[k] = v
  }
  return params
}

const params = loadParams()
const HUB_WG_IP = '10.10.0.1'
const HUB_USER  = 'you'
const HUB_HOSTNAME = 'saconsole'

const REQUIRED_SYNC_ROWS = [
  "✅  MCP grafana",
  "✅  hub: 'prometheus' — up",
  "✅  hub: 'grafana' — up",
  "✅  hub: 'loki' — up",
  "✅  hub: 'promtail' — up",
  "✅  hub: 'alertmanager' — up",
  "✅  hub: 'node_exporter' — up",
  "✅  hub: 'cadvisor' — up",
  "✅  hub: 'mcp-grafana' — up",
]

// Headless by default — the 3–4h rebuild is machine-observed, not human-watched.
// Override with HEADED=1 when debugging locally.
test.use({ headless: process.env.HEADED !== '1' })

test.describe('Acceptance Run 01 — CLI saconsole rebuild', () => {
  // Per-test override of the global 40-min playwright.config timeout.
  // Budget: wait_budget_seconds (rebuild subprocess) + convergence + 10 min margin.
  test.setTimeout(
    (params.wait_budget_seconds + params.topology_convergence_budget_seconds + 600) * 1000
  )

  test('rebuild_saconsole.sh all — exit 0, UI converges, hub + 8 obs + 5 WG peers green', async ({ page }) => {
    // ── Step 1: precondition + baseline ────────────────────────────────────
    await page.goto(BASE_URL)
    await waitForGraph(page)

    const baselineResp = await page.request.get(`${API_URL}/api/hosts`)
    expect(baselineResp.ok(), '/api/hosts baseline').toBe(true)
    const baseline = await baselineResp.json()

    const hub = baseline.hosts.find(h => h.hostname === HUB_HOSTNAME)
    expect(hub, `${HUB_HOSTNAME} must exist in baseline`).toBeTruthy()
    expect(hub.wg_role, `${HUB_HOSTNAME} wg_role`).toBe('hub')
    expect(hub.vm_state, `${HUB_HOSTNAME} must be running at baseline`).toBe('running')

    const baselineSpokes = baseline.hosts
      .filter(h => h.wg_role === 'spoke')
      .map(h => h.hostname)
      .sort()
    console.log(`[accept-01] baseline spokes: ${JSON.stringify(baselineSpokes)}`)

    // UI should show hub node
    const hubOnGraph = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, HUB_HOSTNAME)
    expect(hubOnGraph, `${HUB_HOSTNAME} must be present in Cytoscape at baseline`).toBe(true)

    // ── Step 2: spawn rebuild ──────────────────────────────────────────────
    console.log(
      `[accept-01] spawning: bash platforms/kvm/rebuild_saconsole.sh  ` +
      `(wait budget: ${params.wait_budget_seconds}s)`
    )
    const startedAt = Date.now()
    const proc = spawn('bash', ['platforms/kvm/rebuild_saconsole.sh'], {
      cwd: PROJECT_ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env },
    })

    let stderrTail = ''
    proc.stdout.on('data', d => process.stdout.write(d))
    proc.stderr.on('data', d => {
      const s = d.toString()
      process.stderr.write(s)
      stderrTail = (stderrTail + s).slice(-2000)
    })

    const exitCode = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        proc.kill('SIGKILL')
        reject(new Error(
          `rebuild_saconsole.sh exceeded wait_budget_seconds=${params.wait_budget_seconds}`
        ))
      }, params.wait_budget_seconds * 1000)
      proc.on('exit', code => { clearTimeout(timer); resolve(code) })
      proc.on('error', err => { clearTimeout(timer); reject(err) })
    })

    const rebuildSeconds = Math.round((Date.now() - startedAt) / 1000)
    console.log(`[accept-01] rebuild_saconsole.sh exited code=${exitCode} after ${rebuildSeconds}s`)
    expect(
      exitCode,
      `rebuild_saconsole.sh exit (stderr tail: ${stderrTail})`
    ).toBe(0)

    // ── Step 3: topology convergence ───────────────────────────────────────
    console.log(
      `[accept-01] awaiting UI convergence within ${params.topology_convergence_budget_seconds}s`
    )
    const convergenceStart = Date.now()
    await expect(async () => {
      const r = await page.request.get(`${API_URL}/api/hosts`)
      const data = await r.json()
      const h = data.hosts.find(x => x.hostname === HUB_HOSTNAME)
      expect(h, `${HUB_HOSTNAME} in /api/hosts`).toBeTruthy()
      expect(h.provisioned, `${HUB_HOSTNAME} provisioned`).toBe(true)
      expect(h.vm_state, `${HUB_HOSTNAME} vm_state`).toBe('running')
    }).toPass({
      timeout: params.topology_convergence_budget_seconds * 1000,
      intervals: [5_000],
    })
    const convergenceSeconds = Math.round((Date.now() - convergenceStart) / 1000)
    console.log(`[accept-01] UI converged after ${convergenceSeconds}s`)

    // ── Step 4: backend health — WG peers, obs containers, sync_check ──────
    const wgPeersRaw = execSync(
      `ssh -o BatchMode=yes ${HUB_USER}@${HUB_WG_IP} 'sudo wg show wg0 | grep -c "^peer:"'`,
      { cwd: PROJECT_ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }
    ).trim()
    expect(parseInt(wgPeersRaw, 10), 'hub WG peer count').toBe(5)

    const obsUpRaw = execSync(
      `ssh -o BatchMode=yes ${HUB_USER}@${HUB_WG_IP} 'docker ps --format "{{.Status}}" | grep -c "^Up"'`,
      { cwd: PROJECT_ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }
    ).trim()
    expect(parseInt(obsUpRaw, 10), 'obs containers Up').toBe(8)

    const syncOut = execSync('bash platforms/kvm/sync_check.sh', {
      cwd: PROJECT_ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    })
    for (const req of REQUIRED_SYNC_ROWS) {
      expect(syncOut, `sync_check missing row: ${req}`).toContain(req)
    }

    // ── Step 5: blast radius — pre-existing spokes still present ───────────
    const postResp = await page.request.get(`${API_URL}/api/hosts`)
    const post = await postResp.json()
    const postSpokes = post.hosts
      .filter(h => h.wg_role === 'spoke')
      .map(h => h.hostname)
      .sort()
    for (const s of baselineSpokes) {
      expect(
        postSpokes,
        `pre-existing spoke '${s}' missing after rebuild (blast-radius violation)`
      ).toContain(s)
    }
  })
})
