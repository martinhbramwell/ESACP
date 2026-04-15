// @ts-check
import { test, expect } from '@playwright/test'
import { BASE_URL, API_URL, waitForGraph, selectNode, waitForJob } from './helpers.js'

/**
 * ESACP Topology UI — Generic ERPNext Template tests
 *
 * Tests for the Generic ERPNext template dialog: visibility, form validation,
 * wizard mode selection, and "Use existing" (golden backup) deploy path.
 *
 * Usage:
 *   npx playwright test tests/generic-template.spec.js
 *   npx playwright test tests/generic-template.spec.js --grep "dialog"
 *   npx playwright test tests/generic-template.spec.js --grep "existing"
 */

// ── Helpers ─────────────────────────────────────────────────────────────────

/** Click the Generic ERPNext template tile and open the Deploy dialog via "Create VM". */
async function openGenericDialog(page) {
  await page.evaluate(() => {
    const cy = document.querySelector('#cy')?._cyreg?.cy
    if (!cy) throw new Error('Cytoscape instance not found')
    const tpl = cy.$('#tpl-erpnext-generic')
    if (tpl.empty()) throw new Error('Generic ERPNext template tile not found')
    tpl.emit('tap')
  })
  await page.waitForTimeout(500)

  const btn = page.locator('#info-panel button', { hasText: 'Create VM' })
  await btn.waitFor({ state: 'visible', timeout: 5_000 })
  await btn.click()
  await page.waitForSelector('#dialog-overlay:not(.hidden)', { timeout: 5_000 })
}

/** Open Generic dialog via drag-to-zone (drop in Development zone). */
async function openGenericDialogViaDrag(page) {
  await page.evaluate(() => {
    const cy = document.querySelector('#cy')?._cyreg?.cy
    if (!cy) throw new Error('Cytoscape instance not found')
    const tpl = cy.$('#tpl-erpnext-generic')
    if (tpl.empty()) throw new Error('Generic ERPNext template tile not found')
    tpl.position({ x: 600, y: 200 })
    tpl.emit('dragfree')
  })
  await page.waitForSelector('#dialog-overlay:not(.hidden)', { timeout: 5_000 })
}

// ── Dialog visibility and structure ─────────────────────────────────────────

test.describe('Generic ERPNext — dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
    await waitForGraph(page)
  })

  test('opens with correct title via Create VM button', async ({ page }) => {
    await openGenericDialog(page)
    await expect(page.locator('#dialog-title')).toHaveText('Deploy Generic ERPNext')
  })

  test('opens with correct title via drag-to-zone', async ({ page }) => {
    await openGenericDialogViaDrag(page)
    await expect(page.locator('#dialog-title')).toHaveText('Deploy Generic ERPNext')
  })

  test('shows nickname field and wizard options', async ({ page }) => {
    await openGenericDialog(page)

    // Nickname field visible and required
    const nickname = page.locator('#f-nickname')
    await expect(nickname).toBeVisible()
    await expect(nickname).toHaveAttribute('required', '')

    // Nickname hint visible
    await expect(page.locator('#f-nickname-hint')).toBeVisible()

    // Site URL preview visible
    await expect(page.locator('#field-site-url-preview')).toBeVisible()

    // Wizard options fieldset visible with three radio buttons
    const wizardOpts = page.locator('#wizard-options')
    await expect(wizardOpts).toBeVisible()
    const radios = wizardOpts.locator('input[name="wizard_mode"]')
    await expect(radios).toHaveCount(3)

    // "Record" is checked by default
    const recordRadio = page.locator('input[name="wizard_mode"][value="record"]')
    await expect(recordRadio).toBeChecked()
  })

  test('hostname and nickname have autocomplete disabled', async ({ page }) => {
    await openGenericDialog(page)
    await expect(page.locator('#f-hostname')).toHaveAttribute('autocomplete', 'off')
    await expect(page.locator('#f-nickname')).toHaveAttribute('autocomplete', 'off')
  })

  test('site URL preview updates as hostname is typed', async ({ page }) => {
    await openGenericDialog(page)
    await page.fill('#f-hostname', 'target9')
    await expect(page.locator('#site-url-preview')).toContainText('target9.iridium.blue')
  })

  test('cancel closes dialog and snaps template tile back', async ({ page }) => {
    await openGenericDialogViaDrag(page)
    await page.click('#dialog-cancel')
    await page.waitForSelector('#dialog-overlay', { state: 'hidden', timeout: 5_000 })

    // Template tile snaps back via a 200ms setTimeout — wait for it
    await page.waitForTimeout(500)

    const pos = await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy?.$('#tpl-erpnext-generic').position()
    })
    // Home position is { x: 160, y: 280 } — should be back in Console quadrant
    expect(pos.x).toBeLessThan(400)
  })
})

// ── Form validation ─────────────────────────────────────────────────────────

test.describe('Generic ERPNext — validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
    await waitForGraph(page)
    await openGenericDialog(page)
  })

  test('submit button says Deploy', async ({ page }) => {
    await expect(page.locator('#dialog-submit')).toHaveText('Deploy')
  })

  test('rejects empty hostname', async ({ page }) => {
    await page.fill('#f-nickname', 'T9IRBL')
    await page.click('#dialog-submit')
    // Form validation should prevent submission — dialog stays open
    await expect(page.locator('#dialog-overlay')).not.toHaveClass(/hidden/)
  })

  test('rejects empty nickname', async ({ page }) => {
    await page.fill('#f-hostname', 'target9')
    await page.fill('#f-nickname', '')
    await page.click('#dialog-submit')
    // Dialog stays open — nickname is required for templates
    await expect(page.locator('#dialog-overlay')).not.toHaveClass(/hidden/)
  })

  test('rejects invalid hostname pattern', async ({ page }) => {
    await page.fill('#f-hostname', 'Target9')  // uppercase not allowed
    await page.fill('#f-nickname', 'T9IRBL')
    await page.click('#dialog-submit')
    await expect(page.locator('#dialog-overlay')).not.toHaveClass(/hidden/)
  })
})

// ── Wizard mode switching ───────────────────────────────────────────────────

test.describe('Generic ERPNext — wizard modes', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
    await waitForGraph(page)
    await openGenericDialog(page)
  })

  test('replay mode shows recording dropdown', async ({ page }) => {
    await page.click('input[name="wizard_mode"][value="replay"]')
    await expect(page.locator('#wizard-replay-select')).toBeVisible()
    await expect(page.locator('#wizard-existing-select')).not.toBeVisible()
  })

  test('existing mode shows backup dropdown', async ({ page }) => {
    await page.click('input[name="wizard_mode"][value="existing"]')
    await expect(page.locator('#wizard-existing-select')).toBeVisible()
    await expect(page.locator('#wizard-replay-select')).not.toBeVisible()
  })

  test('record mode hides both dropdowns', async ({ page }) => {
    // Switch to replay first, then back to record
    await page.click('input[name="wizard_mode"][value="replay"]')
    await page.click('input[name="wizard_mode"][value="record"]')
    await expect(page.locator('#wizard-replay-select')).not.toBeVisible()
    await expect(page.locator('#wizard-existing-select')).not.toBeVisible()
  })

  test('replay mode rejects empty recording selection', async ({ page }) => {
    await page.fill('#f-hostname', 'target9')
    await page.fill('#f-nickname', 'T9IRBL')
    await page.click('input[name="wizard_mode"][value="replay"]')

    // Clear the select to ensure no recording is chosen
    await page.evaluate(() => {
      const sel = document.getElementById('f-wizard-recording')
      if (sel) sel.value = ''
    })

    await page.click('#dialog-submit')
    // Should show error about missing recording
    await expect(page.locator('#dialog-error')).toBeVisible()
    await expect(page.locator('#dialog-error')).toContainText('recording')
  })

  test('existing mode rejects empty backup selection', async ({ page }) => {
    await page.fill('#f-hostname', 'target9')
    await page.fill('#f-nickname', 'T9IRBL')
    await page.click('input[name="wizard_mode"][value="existing"]')

    await page.evaluate(() => {
      const sel = document.getElementById('f-wizard-backup')
      if (sel) sel.value = ''
    })

    await page.click('#dialog-submit')
    await expect(page.locator('#dialog-error')).toBeVisible()
    await expect(page.locator('#dialog-error')).toContainText('backup')
  })
})

// ── Use existing — e2e deploy with golden backup ────────────────────────────

test.describe('Generic ERPNext — Use existing e2e', () => {
  const hostname   = process.env.GENERIC_HOSTNAME   || 'target5'
  const nickname   = process.env.GENERIC_NICKNAME    || 'D1IRBL'
  const wgIp       = process.env.GENERIC_WG_IP      || '10.10.0.15'
  const virbr0Ip   = process.env.GENERIC_VIRBR0_IP  || '192.168.122.25'

  test('deploys VM with golden backup and reaches ERPNext', async ({ page }) => {
    // Check that a golden backup is available
    const backupResp = await page.request.get(`${API_URL}/api/golden-backups`)
    const backups = await backupResp.json()
    test.skip(!backups.length, 'No golden backups available — skipping e2e')
    const backupFile = backups[0].filename

    await page.goto(BASE_URL)
    await waitForGraph(page)

    // If the target hostname already exists and is provisioned, destroy it first
    const preflight = await page.request.get(`${API_URL}/api/hosts`)
    const pfData = await preflight.json()
    const existing = pfData.hosts.find(h => h.hostname === hostname)
    if (existing && existing.provisioned) {
      await selectNode(page, hostname)
      const destroyBtn = page.locator('#info-panel button', { hasText: 'Destroy' })
      await destroyBtn.click()
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

    // Open the Generic ERPNext dialog
    await openGenericDialog(page)

    // Fill the form
    await page.fill('#f-hostname', hostname)
    await page.fill('#f-nickname', nickname)
    await page.fill('#f-wg-ip', wgIp)
    await page.fill('#f-virbr0-ip', virbr0Ip)

    // Select "Use existing" wizard mode
    await page.click('input[name="wizard_mode"][value="existing"]')
    await page.waitForSelector('#wizard-existing-select:not([style*="display: none"])', { timeout: 3_000 })

    // Pick the first available backup
    await page.selectOption('#f-wizard-backup', backupFile)

    // Submit
    await page.click('#dialog-submit')
    await page.waitForSelector('#dialog-overlay', { state: 'hidden', timeout: 10_000 })

    // Verify job started
    await page.waitForTimeout(2_000)
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const activeJob = Object.entries(jobs).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    )
    expect(activeJob).toBeTruthy()
    const [jobId] = activeJob

    // Wait for provisioning to complete (up to 35 min)
    await waitForJob(page, jobId, 2_100_000)

    // Verify node is provisioned
    const resp2 = await page.request.get(`${API_URL}/api/hosts`)
    const data2 = await resp2.json()
    const host = data2.hosts.find(h => h.hostname === hostname)
    expect(host).toBeTruthy()
    expect(host.provisioned).toBe(true)
    expect(host.erp_url).toBeTruthy()
  })
})
