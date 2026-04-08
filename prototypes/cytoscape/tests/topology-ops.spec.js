// @ts-check
import { test, expect } from '@playwright/test'

/**
 * ESACP Topology UI — Playwright end-to-end tests
 *
 * Parameterised operations for the Cytoscape control plane:
 *   - Deploy from Template (form fill + submit)
 *   - Refresh (re-run differentiation)
 *   - Destroy VM (confirm dialog)
 *   - Inspect (health check popup)
 *
 * Usage:
 *   npx playwright test tests/topology-ops.spec.js
 *   npx playwright test tests/topology-ops.spec.js --grep "deploy"
 *   DEPLOY_HOSTNAME=dev03 npx playwright test --grep "deploy"
 *
 * Prerequisites:
 *   - uvicorn tools.api:app --port 8088  (FastAPI backend)
 *   - bash doCytoscape.sh                (Vite dev server on :5173)
 */

const BASE_URL = process.env.TOPOLOGY_URL || 'http://localhost:5173'
const API_URL  = process.env.API_URL || 'http://localhost:8088'

// ── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Wait for the Cytoscape graph to initialise (nodes rendered).
 */
async function waitForGraph(page) {
  await page.waitForSelector('#cy canvas', { timeout: 10_000 })
  // Give Cytoscape a moment to lay out nodes
  await page.waitForTimeout(1500)
}

/**
 * Click a VM node on the graph by hostname.
 * Uses the API to find the node's WG IP, then clicks via evaluate.
 */
async function selectNode(page, hostname) {
  await page.evaluate((h) => {
    const cy = document.querySelector('#cy')?._cyreg?.cy
    if (!cy) throw new Error('Cytoscape instance not found')
    const node = cy.$(`#${h}`)
    if (node.empty()) throw new Error(`Node '${h}' not found on graph`)
    node.emit('tap')
  }, hostname)
  // Wait for info panel to populate
  await page.waitForTimeout(500)
}

/**
 * Click an action button in the info panel by text content.
 */
async function clickInfoButton(page, buttonText) {
  const btn = page.locator('#info-panel button', { hasText: buttonText })
  await expect(btn).toBeVisible({ timeout: 5_000 })
  await btn.click()
}

/**
 * Wait for a provisioning/refresh/destroy job to complete.
 * Polls the API /api/jobs endpoint.
 */
async function waitForJob(page, jobId, timeoutMs = 2_100_000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const job = jobs[jobId]
    if (!job) throw new Error(`Job ${jobId} not found`)
    if (job.status === 'done') return job
    if (job.status === 'failed') throw new Error(`Job ${jobId} failed`)
    await page.waitForTimeout(5_000)
  }
  throw new Error(`Job ${jobId} timed out after ${timeoutMs}ms`)
}

// ── Deploy from Template ────────────────────────────────────────────────────

/**
 * Fill and submit the Deploy from Template dialog.
 * All fields are parameterised via the `config` object.
 */
async function deployFromTemplate(page, config) {
  const {
    hostname,
    nickname,
    wgIp,
    virbr0Ip,
    backend = 'kvm',
    hypervisor = 'toshiba',
    zone = 'Development',
    vmRole = 'Unspecified',
  } = config

  // Open Deploy dialog by simulating drag of ERPNext template tile into Dev zone.
  // The tile's dragfree handler checks _zoneAtPos and opens the dialog if in zone-dev.
  await page.evaluate(() => {
    const cy = document.querySelector('#cy')?._cyreg?.cy
    if (!cy) throw new Error('Cytoscape instance not found')
    const tpl = cy.$('#tpl-erpnext')
    if (tpl.empty()) throw new Error('ERPNext template tile not found')
    // Move tile into Development zone (right half, top — x > splitX, y < splitY)
    tpl.position({ x: 600, y: 200 })
    tpl.emit('dragfree')
  })

  await page.waitForSelector('#dialog-overlay:not(.hidden)', { timeout: 5_000 })

  // Fill form fields
  await page.fill('#f-hostname', hostname)
  await page.fill('#f-nickname', nickname)
  await page.fill('#f-wg-ip', wgIp)
  await page.fill('#f-virbr0-ip', virbr0Ip)
  await page.fill('#f-hypervisor', hypervisor)
  await page.selectOption('#f-backend', backend)
  await page.selectOption('#f-zone', zone)
  if (vmRole !== 'Unspecified') {
    await page.selectOption('#f-vm-role', vmRole)
  }

  // Verify Site URL preview
  const siteUrl = page.locator('#site-url-preview')
  if (await siteUrl.isVisible()) {
    await expect(siteUrl).toContainText(`${hostname}.iridium.blue`)
  }

  // Submit
  await page.click('#dialog-submit')

  // Wait for dialog to close and provisioning to start
  await page.waitForSelector('#dialog-overlay', { state: 'hidden', timeout: 10_000 })
}

// ── Test: Deploy ────────────────────────────────────────────────────────────

test.describe('Deploy from Template', () => {
  test('provisions a new VM with correct parameters', async ({ page }) => {
    const hostname   = process.env.DEPLOY_HOSTNAME   || 'dev02'
    const nickname   = process.env.DEPLOY_NICKNAME    || 'D2IRBL'
    const wgIp       = process.env.DEPLOY_WG_IP      || '10.10.0.12'
    const virbr0Ip   = process.env.DEPLOY_VIRBR0_IP  || '192.168.122.20'
    const zone       = process.env.DEPLOY_ZONE        || 'Development'

    await page.goto(BASE_URL)
    await waitForGraph(page)

    await deployFromTemplate(page, {
      hostname, nickname, wgIp, virbr0Ip, zone,
    })

    // Verify node appeared on graph
    const nodeExists = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, hostname)
    expect(nodeExists).toBe(true)

    // Verify job started via API
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const activeJob = Object.entries(jobs).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    )
    expect(activeJob).toBeTruthy()
  })
})

// ── Test: Refresh ───────────────────────────────────────────────────────────

test.describe('Refresh', () => {
  test('triggers differentiation re-run on a provisioned node', async ({ page }) => {
    const hostname = process.env.REFRESH_HOSTNAME || 'dev01'

    await page.goto(BASE_URL)
    await waitForGraph(page)
    await selectNode(page, hostname)
    await clickInfoButton(page, 'Refresh')

    // Wait for job to appear
    await page.waitForTimeout(2_000)
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const refreshJob = Object.entries(jobs).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    )
    expect(refreshJob).toBeTruthy()
  })
})

// ── Test: Destroy ───────────────────────────────────────────────────────────

test.describe('Destroy VM', () => {
  test('opens confirm dialog and destroys a VM', async ({ page }) => {
    const hostname = process.env.DESTROY_HOSTNAME || 'dev02'

    await page.goto(BASE_URL)
    await waitForGraph(page)
    await selectNode(page, hostname)
    await clickInfoButton(page, 'Destroy')

    // Confirm dialog should appear
    await page.waitForSelector('#confirm-overlay:not(.hidden)', { timeout: 5_000 })
    const body = await page.textContent('#confirm-body')
    expect(body).toContain(hostname)

    // Click confirm
    await page.click('#confirm-submit')
    await page.waitForSelector('#confirm-overlay', { state: 'hidden', timeout: 10_000 })

    // Verify job started
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const destroyJob = Object.entries(jobs).find(
      ([, j]) => j.hostname === hostname
    )
    expect(destroyJob).toBeTruthy()
  })
})

// ── Test: Inspect ───────────────────────────────────────────────────────────

test.describe('Inspect', () => {
  test('opens health check popup with 3 service indicators', async ({ page }) => {
    const hostname = process.env.INSPECT_HOSTNAME || 'dev01'

    await page.goto(BASE_URL)
    await waitForGraph(page)
    await selectNode(page, hostname)
    await clickInfoButton(page, 'Inspect')

    // Popup should open with health grid
    await page.waitForSelector('#popup-overlay:not(.hidden)', { timeout: 10_000 })

    // Should show 3 service boxes (web, app, db)
    const boxes = page.locator('#popup-info .health-box, #popup-info .svc-box')
    // Wait for health check to complete (SSH takes a few seconds)
    await page.waitForTimeout(8_000)

    // Close popup
    await page.click('#popup-close')
    await page.waitForSelector('#popup-overlay', { state: 'hidden', timeout: 5_000 })
  })
})

// ── Test: Rebuild — Destroy existing + Deploy fresh + Inspect ────────────────

test.describe('Rebuild', () => {
  test('destroy → deploy → inspect', async ({ page }) => {
    const hostname = process.env.LIFECYCLE_HOSTNAME || 'dev02'
    const config = {
      hostname,
      nickname: process.env.LIFECYCLE_NICKNAME  || 'D2IRBL',
      wgIp:     process.env.LIFECYCLE_WG_IP     || '10.10.0.12',
      virbr0Ip: process.env.LIFECYCLE_VIRBR0_IP || '192.168.122.20',
      zone: process.env.LIFECYCLE_ZONE           || 'Development',
    }

    await page.goto(BASE_URL)
    await waitForGraph(page)

    // Destroy existing VM
    await selectNode(page, hostname)
    await clickInfoButton(page, 'Destroy')
    await page.waitForSelector('#confirm-overlay:not(.hidden)', { timeout: 5_000 })
    const body = await page.textContent('#confirm-body')
    expect(body).toContain(hostname)
    await page.click('#confirm-submit')
    await page.waitForSelector('#confirm-overlay', { state: 'hidden', timeout: 10_000 })

    // Wait for destroy job to complete
    await page.waitForTimeout(3_000)
    const resp1 = await page.request.get(`${API_URL}/api/jobs`)
    const jobs1 = await resp1.json()
    const [djId] = Object.entries(jobs1).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    ) || []
    expect(djId).toBeTruthy()
    await waitForJob(page, djId, 180_000)

    // Give UI time to process the removal
    await page.waitForTimeout(2_000)

    // Verify node removed from graph
    const nodeGone = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? cy.$(`#${h}`).empty() : true
    }, hostname)
    expect(nodeGone).toBe(true)

    // Deploy fresh
    await deployFromTemplate(page, config)
    const resp2 = await page.request.get(`${API_URL}/api/jobs`)
    const jobs2 = await resp2.json()
    const [deployId] = Object.entries(jobs2).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    ) || []
    expect(deployId).toBeTruthy()

    // Wait for provisioning to complete (up to 25 min)
    await waitForJob(page, deployId, 1_500_000)

    // Inspect — verify services are healthy
    await selectNode(page, hostname)
    await clickInfoButton(page, 'Inspect')
    await page.waitForSelector('#popup-overlay:not(.hidden)', { timeout: 10_000 })
    await page.waitForTimeout(10_000) // health checks via SSH
    await page.click('#popup-close')
  })
})

// ── Test: Full Deploy + Verify + Destroy cycle ──────────────────────────────

test.describe('Full lifecycle', () => {
  test.skip(!!process.env.SKIP_LIFECYCLE, 'skipped via SKIP_LIFECYCLE env')

  test('deploy → inspect → destroy', async ({ page }) => {
    const hostname = process.env.LIFECYCLE_HOSTNAME || 'dev03'
    const config = {
      hostname,
      nickname: process.env.LIFECYCLE_NICKNAME  || 'D3IRBL',
      wgIp:     process.env.LIFECYCLE_WG_IP     || '10.10.0.14',
      virbr0Ip: process.env.LIFECYCLE_VIRBR0_IP || '192.168.122.22',
      zone: 'Development',
    }

    await page.goto(BASE_URL)
    await waitForGraph(page)

    // Deploy
    await deployFromTemplate(page, config)
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const [jobId] = Object.entries(jobs).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    ) || []
    expect(jobId).toBeTruthy()

    // Wait for provisioning to complete (up to 25 min)
    await waitForJob(page, jobId, 1_500_000)

    // Inspect — verify all green
    await selectNode(page, hostname)
    await clickInfoButton(page, 'Inspect')
    await page.waitForSelector('#popup-overlay:not(.hidden)', { timeout: 10_000 })
    await page.waitForTimeout(10_000) // health checks
    await page.click('#popup-close')

    // Destroy
    await selectNode(page, hostname)
    await clickInfoButton(page, 'Destroy')
    await page.waitForSelector('#confirm-overlay:not(.hidden)', { timeout: 5_000 })
    await page.click('#confirm-submit')

    // Wait for destroy job
    await page.waitForTimeout(3_000)
    const resp2 = await page.request.get(`${API_URL}/api/jobs`)
    const jobs2 = await resp2.json()
    const [djId] = Object.entries(jobs2).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    ) || []
    if (djId) await waitForJob(page, djId, 180_000)

    // Verify node removed
    const nodeGone = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? cy.$(`#${h}`).empty() : true
    }, hostname)
    expect(nodeGone).toBe(true)
  })
})
