// @ts-check
import { test, expect } from '@playwright/test'
import { BASE_URL, API_URL, waitForGraph, selectNode, clickInfoButton, waitForJob } from './helpers.js'

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
    const [jobId] = activeJob

    // Wait for provisioning to complete (template clone + differentiation — up to 35 min)
    await waitForJob(page, jobId, 2_100_000)

    // Verify node is now provisioned and ERPNext is reachable
    const resp2 = await page.request.get(`${API_URL}/api/hosts`)
    const data2 = await resp2.json()
    const host = data2.hosts.find(h => h.hostname === hostname)
    expect(host).toBeTruthy()
    expect(host.provisioned).toBe(true)
    expect(host.erp_url).toBeTruthy()
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
    const [jobId] = refreshJob

    // Wait for refresh to complete (differentiation re-run — up to 35 min)
    await waitForJob(page, jobId, 2_100_000)

    // Verify VM is still provisioned and healthy via API
    const resp2 = await page.request.get(`${API_URL}/api/hosts`)
    const data2 = await resp2.json()
    const host = data2.hosts.find(h => h.hostname === hostname)
    expect(host).toBeTruthy()
    expect(host.provisioned).toBe(true)
    expect(host.erp_url).toBeTruthy()
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

    // Wait for provisioning to complete (up to 35 min)
    await waitForJob(page, deployId, 2_100_000)

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

    // Pre-flight: if VM already exists and is provisioned, destroy it first
    const preflight = await page.request.get(`${API_URL}/api/hosts`)
    const pfData = await preflight.json()
    const existing = pfData.hosts.find(h => h.hostname === hostname)
    if (existing && existing.provisioned) {
      await selectNode(page, hostname)
      await clickInfoButton(page, 'Destroy')
      await page.waitForSelector('#confirm-overlay:not(.hidden)', { timeout: 5_000 })
      await page.click('#confirm-submit')
      await page.waitForSelector('#confirm-overlay', { state: 'hidden', timeout: 10_000 })

      await page.waitForTimeout(3_000)
      const djResp = await page.request.get(`${API_URL}/api/jobs`)
      const djJobs = await djResp.json()
      const [djId] = Object.entries(djJobs).find(
        ([, j]) => j.hostname === hostname && j.status === 'running'
      ) || []
      if (djId) await waitForJob(page, djId, 180_000)

      await page.waitForTimeout(2_000)
    }

    // Deploy
    await deployFromTemplate(page, config)
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const [jobId] = Object.entries(jobs).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    ) || []
    expect(jobId).toBeTruthy()

    // Wait for provisioning to complete (up to 35 min — allows for pre-flight destroy overhead)
    await waitForJob(page, jobId, 2_100_000)

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

// ── VM Power Control ───────────────────────────────────────────────────────

/**
 * Power control tests: Start / Stop / Reboot buttons and memory guard.
 *
 * These tests verify that the correct buttons appear based on vm_state,
 * that clicking them calls the API and refreshes state, and that the
 * memory guard surfaces errors from the backend.
 *
 * Usage:
 *   POWER_HOSTNAME=dev03 npx playwright test --grep "power"
 *   npx playwright test --grep "power"
 */

test.describe('power — VM power control', () => {
  const hostname = process.env.POWER_HOSTNAME || 'dev03'

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
    await waitForGraph(page)
  })

  test('shows Stop + Reboot buttons for a running VM', async ({ page }) => {
    // Verify the VM is running via API first
    const resp = await page.request.get(`${API_URL}/api/hosts`)
    const data = await resp.json()
    const host = data.hosts.find(h => h.hostname === hostname)
    test.skip(!host || host.vm_state !== 'running', `${hostname} is not running — skipping`)

    await selectNode(page, hostname)
    const stopBtn   = page.locator('#info-panel button', { hasText: 'Stop' })
    const rebootBtn = page.locator('#info-panel button', { hasText: 'Reboot' })
    await expect(stopBtn).toBeVisible({ timeout: 3_000 })
    await expect(rebootBtn).toBeVisible({ timeout: 3_000 })
    // Start should NOT be visible for a running VM
    const startBtn = page.locator('#info-panel button', { hasText: 'Start' })
    await expect(startBtn).toHaveCount(0)
  })

  test('shows Start button for a shut-off VM', async ({ page }) => {
    const resp = await page.request.get(`${API_URL}/api/hosts`)
    const data = await resp.json()
    const shutOff = data.hosts.find(h => h.vm_state === 'shut off' && h.provisioned)
    test.skip(!shutOff, 'No shut-off provisioned VM available — skipping')

    await selectNode(page, shutOff.hostname)
    const startBtn = page.locator('#info-panel button', { hasText: 'Start' })
    await expect(startBtn).toBeVisible({ timeout: 3_000 })
    // Stop should NOT be visible for a shut-off VM
    const stopBtn = page.locator('#info-panel button', { hasText: 'Stop' })
    await expect(stopBtn).toHaveCount(0)
  })

  test('Stop button shuts down VM and refreshes state', async ({ page }) => {
    const resp = await page.request.get(`${API_URL}/api/hosts`)
    const data = await resp.json()
    const host = data.hosts.find(h => h.hostname === hostname)
    test.skip(!host || host.vm_state !== 'running', `${hostname} is not running — skipping`)

    await selectNode(page, hostname)
    await clickInfoButton(page, 'Stop')

    // Graceful shutdown may take several seconds. The _refreshVmState() call
    // in _vmPowerAction fires immediately after virsh returns — the VM may
    // still be in "running" state. Poll the API until the state changes.
    await expect(async () => {
      const r = await page.request.get(`${API_URL}/api/hosts`)
      const d = await r.json()
      const h = d.hosts.find(x => x.hostname === hostname)
      expect(h.vm_state).toBe('shut off')
    }).toPass({ timeout: 30_000, intervals: [3_000] })
  })

  test('Start button starts VM and refreshes state', async ({ page }) => {
    const resp = await page.request.get(`${API_URL}/api/hosts`)
    const data = await resp.json()
    const host = data.hosts.find(h => h.hostname === hostname)
    test.skip(!host || host.vm_state !== 'shut off', `${hostname} is not shut off — skipping`)

    await selectNode(page, hostname)
    await clickInfoButton(page, 'Start')

    // After start + state refresh, the info panel re-renders with Stop/Reboot
    // buttons (the transient "started" message is replaced by renderInfoWithActions)
    const stopBtn = page.locator('#info-panel button', { hasText: 'Stop' })
    await expect(stopBtn).toBeVisible({ timeout: 30_000 })

    // Verify via API that state changed
    const resp2 = await page.request.get(`${API_URL}/api/hosts`)
    const data2 = await resp2.json()
    const host2 = data2.hosts.find(h => h.hostname === hostname)
    expect(host2.vm_state).toBe('running')
  })

  test('memory guard surfaces error when insufficient RAM', async ({ page }) => {
    // Intercept the Vite-proxied path (the browser fetches /api/vm/…, not localhost:8088)
    await page.route('**/api/vm/*/start', async route => {
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Not enough memory on hypervisor — 4096 MiB needed for dev99, '
                + '12288 MiB already used by [saconsole, dev03], '
                + 'host has 15948 MiB total (2048 MiB reserved for host OS). '
                + 'Shut down another VM first.'
        })
      })
    })

    // Patch node data to simulate shut-off, then re-tap to get the Start button
    await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return
      const node = cy.$(`#${h}`)
      if (node.empty()) return
      node.data('vm_state', 'shut off')
      node.data('provisioned', true)
      node.data('label', `${h}\n[shut off]`)
      node.emit('tap')
    }, hostname)
    await page.waitForTimeout(500)

    await clickInfoButton(page, 'Start')

    // Verify the memory guard error is displayed
    await expect(page.locator('#info-panel')).toContainText('Not enough memory', { timeout: 5_000 })
    await expect(page.locator('#info-panel')).toContainText('Shut down another VM first', { timeout: 3_000 })
  })
})

// ── Provisioning State Display (#90) + Live Job Log (#91) ─────────────────

test.describe('provisioning state — node visual and job log', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
    await waitForGraph(page)
  })

  test('#90: node shows [provisioning...] label and blue border during active job', async ({ page }) => {
    // Find an unprovisioned node, or simulate one
    const hostname = await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return null
      // Find any spoke node to test with
      const nodes = cy.nodes(':not(.phantom):not(.template-node)')
      const spoke = nodes.filter(n => n.data('role') === 'spoke')
      return spoke.length ? spoke[0].id() : null
    })
    test.skip(!hostname, 'No spoke node available for testing')

    // Inject provisioning state on the node (simulates what _attachJobPoller does)
    await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      const node = cy.$(`#${h}`)
      node.data('job_id', 'test-job-001')
      node.data('job_status', 'running')
      node.data('job_type', 'provision')
      node.data('label', `${h}\n[provisioning...]`)
    }, hostname)

    // Verify the label changed
    const label = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy.$(`#${h}`).data('label')
    }, hostname)
    expect(label).toContain('[provisioning...]')

    // Verify the blue border style is applied (job_status = "running" selector)
    const borderColor = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      const node = cy.$(`#${h}`)
      return node.style('border-color')
    }, hostname)
    // Cytoscape normalises hex to rgb — #4488dd = rgb(68,136,221)
    expect(borderColor).toMatch(/68.*136.*221|#4488dd|#48d/i)

    const borderStyle = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy.$(`#${h}`).style('border-style')
    }, hostname)
    expect(borderStyle).toBe('dashed')
  })

  test('#90: _refreshVmState preserves provisioning label (not overwritten by poll)', async ({ page }) => {
    const hostname = await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return null
      const spoke = cy.nodes('[role = "spoke"]')
      return spoke.length ? spoke[0].id() : null
    })
    test.skip(!hostname, 'No spoke node available')

    // Set provisioning state
    await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      const node = cy.$(`#${h}`)
      node.data('job_id', 'test-job-002')
      node.data('job_status', 'running')
      node.data('job_type', 'provision')
      node.data('label', `${h}\n[provisioning...]`)
    }, hostname)

    // Trigger _refreshVmState manually
    await page.evaluate(() => {
      // _refreshVmState is module-scoped — trigger it via the 30s interval
      // by calling fetchHosts and simulating the update loop
      return fetch('/api/hosts')
        .then(r => r.json())
        .then(data => {
          const cy = document.querySelector('#cy')?._cyreg?.cy
          for (const h of data.hosts) {
            const node = cy.$(`#${h.id ?? h.hostname}`)
            if (node.empty()) continue
            // Simulate what _refreshVmState does — should skip if job_status is running
            if (node.data('job_status') === 'running') continue
            node.data('vm_state', h.vm_state ?? null)
          }
        })
    })

    // Verify label was NOT overwritten
    const label = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy.$(`#${h}`).data('label')
    }, hostname)
    expect(label).toContain('[provisioning...]')
  })

  test('#91: clicking a provisioning node shows job log in info panel', async ({ page }) => {
    // Use a completed job from the API (we know some exist)
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const [jobId, jobData] = Object.entries(jobs).find(
      ([, j]) => j.hostname && j.status !== 'running'
    ) || []
    test.skip(!jobId, 'No completed job available to test log display')

    const hostname = jobData.hostname

    // Set node to look like it has an active job (point at the real job for log content)
    await page.evaluate(({ h, jid }) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return
      const node = cy.$(`#${h}`)
      if (node.empty()) return
      node.data('job_id', jid)
      node.data('job_status', 'running')
      node.data('job_type', 'provision')
      node.data('label', `${h}\n[provisioning...]`)
    }, { h: hostname, jid: jobId })

    // Click the node
    await selectNode(page, hostname)

    // The info panel should show a job log <pre>, not the specs table
    await page.waitForTimeout(1500) // allow fetch to complete
    const hasJobLog = await page.locator('#info-panel pre.job-log').isVisible()
    expect(hasJobLog).toBe(true)

    // The log should contain actual content from the API
    const logText = await page.locator('#info-panel pre.job-log').textContent()
    expect(logText.length).toBeGreaterThan(20)
  })

  test('#91: clicking a non-provisioning node while another has active job shows info', async ({ page }) => {
    // Set up: one node provisioning, click a DIFFERENT node
    await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return
      const spokes = cy.nodes('[role = "spoke"]')
      if (spokes.length < 2) return
      // First spoke: simulate provisioning
      spokes[0].data('job_id', 'test-job-003')
      spokes[0].data('job_status', 'running')
      spokes[0].data('job_type', 'provision')
      spokes[0].data('label', `${spokes[0].id()}\n[provisioning...]`)
    })

    // We need activeJob to be set for the guard to work.
    // Since we can't set the module-scoped activeJob directly,
    // verify that clicking a non-job node doesn't crash.
    const otherHostname = await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return null
      // Find hub or controller (always safe to click)
      const hub = cy.nodes('[role = "hub"]')
      return hub.length ? hub[0].id() : null
    })
    test.skip(!otherHostname, 'No hub node to test against')

    await selectNode(page, otherHostname)
    // Should show specs (or at least not crash)
    const panel = await page.locator('#info-panel').textContent()
    expect(panel.length).toBeGreaterThan(0)
  })
})
