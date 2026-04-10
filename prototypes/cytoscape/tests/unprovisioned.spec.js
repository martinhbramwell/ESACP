// @ts-check
import { test, expect } from '@playwright/test'
import { BASE_URL, API_URL, waitForGraph, selectNode, waitForJob } from './helpers.js'

/**
 * #143 — Unprovisioned node: button guards + e2e Provision
 *
 * Usage:
 *   npx playwright test tests/unprovisioned.spec.js
 *   PROVISION_HOSTNAME=target3 npx playwright test --grep "e2e"
 */

// ── Negative test: button visibility on unprovisioned node ──────────────────

test.describe('unprovisioned node — button guards', () => {
  test('Refresh absent, Provision + Destroy present', async ({ page }) => {
    await page.goto(BASE_URL)
    await waitForGraph(page)

    const hostname = await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return null
      const unprov = cy.nodes('[role = "spoke"][!provisioned]:not(.phantom):not(.template-node)')
      if (unprov.length) return unprov[0].id()
      const spoke = cy.nodes('[role = "spoke"]:not(.phantom):not(.template-node)')
      if (!spoke.length) return null
      const h = spoke[0].id()
      spoke[0].data('provisioned', false)
      spoke[0].data('erp_url', null)
      spoke[0].data('label', `${h}\n[unprovisioned]`)
      return h
    })
    test.skip(!hostname, 'No spoke node available')

    await selectNode(page, hostname)

    const panel = page.locator('#info-panel')
    await expect(panel.locator('button', { hasText: 'Provision' })).toBeVisible({ timeout: 3_000 })
    await expect(panel.locator('button', { hasText: 'Destroy' })).toBeVisible({ timeout: 3_000 })
    for (const absent of ['Refresh', 'Start', 'Stop', 'Reboot', 'Inspect']) {
      await expect(panel.locator('button', { hasText: absent })).toHaveCount(0)
    }
  })
})

// ── E2e: Provision an unprovisioned VM via cloud-init path ──────────────────

test.describe('Provision unprovisioned VM (e2e)', () => {
  test('Provision button starts job, waits for completion', async ({ page }) => {
    const hostname = process.env.PROVISION_HOSTNAME || 'target3'

    await page.goto(BASE_URL)
    await waitForGraph(page)

    const nodeState = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) return null
      const node = cy.$(`#${h}`)
      if (node.empty()) return null
      return { provisioned: node.data('provisioned') }
    }, hostname)
    test.skip(!nodeState, `'${hostname}' not on graph`)
    test.skip(nodeState.provisioned === true, `'${hostname}' already provisioned`)

    await selectNode(page, hostname)
    const provBtn = page.locator('#info-panel button', { hasText: 'Provision' })
    await expect(provBtn).toBeVisible({ timeout: 3_000 })
    await provBtn.click()

    await expect(page.locator('#info-panel pre.job-log')).toBeVisible({ timeout: 5_000 })

    await page.waitForTimeout(3_000)
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const [jobId] = Object.entries(jobs).find(
      ([, j]) => j.hostname === hostname && j.status === 'running'
    ) || []
    expect(jobId).toBeTruthy()

    await waitForJob(page, jobId, 900_000)

    const resp2 = await page.request.get(`${API_URL}/api/hosts`)
    const data2 = await resp2.json()
    const host = data2.hosts.find(h => h.hostname === hostname)
    expect(host).toBeTruthy()
    expect(host.provisioned).toBe(true)
  })
})
