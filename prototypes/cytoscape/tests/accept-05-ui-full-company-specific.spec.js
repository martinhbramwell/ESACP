// @ts-check
import { test, expect } from '@playwright/test'
import { execSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { BASE_URL, API_URL, waitForGraph, selectNode, clickInfoButton, waitForJob } from './helpers.js'

/**
 * Acceptance Run 05 — UI dev VM, full company-specific ERPNext from golden production backup.
 *
 * UI drag-to-deploy lifecycle (parity partner: Run 02 CLI):
 *   1. Destroy existing dev01 via Cytoscape: selectNode → Destroy → confirm.
 *   2. Drag tpl-erpnext-restored tile into Dev zone → Deploy from Template dialog.
 *   3. Fill hostname/nickname/IPs/hypervisor/zone → submit → wait for job.
 *
 * Plan:    ~/.claude/plans/acceptance-matrix-transport-parity.md
 * Agenda:  docs/SessionLogs/acceptance-matrix/05-ui-vm-full-company-specific-from-backup.md
 * Params:  docs/SessionLogs/acceptance-matrix/params/05-ui-full-company-specific.yml
 *
 * Parity partner: Run 02 (CLI). Canary asserted verbatim for transport parity.
 *
 * Administrator password: derived automatically from config/build_secrets.sops.yml
 * (field erp_user_pwd). Pipeline resets Administrator post-restore.
 */

const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)
const PROJECT_ROOT = path.resolve(__dirname, '../../..')
const PARAM_PATH = path.join(
  PROJECT_ROOT,
  'docs/SessionLogs/acceptance-matrix/params/05-ui-full-company-specific.yml'
)
const BUILD_SECRETS_PATH = path.join(PROJECT_ROOT, 'config/build_secrets.sops.yml')

function loadParams() {
  const raw = readFileSync(PARAM_PATH, 'utf8')
  const params = {}
  for (const line of raw.split('\n')) {
    const m = line.match(/^\s*([a-z0-9_]+)\s*:\s*(.+?)\s*$/)
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

function decryptBuildSecret(key) {
  const raw = execSync(`sops -d ${BUILD_SECRETS_PATH}`, {
    cwd: PROJECT_ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
  })
  for (const line of raw.split('\n')) {
    const m = line.match(new RegExp(`^\\s*${key}\\s*:\\s*(.+?)\\s*$`))
    if (!m) continue
    const v = m[1].trim()
    const quoted = v.match(/^["'](.*)["']$/)
    return quoted ? quoted[1] : v
  }
  throw new Error(`${key} not found in decrypted ${BUILD_SECRETS_PATH}`)
}

function runSyncCheck() {
  try {
    return execSync('bash platforms/kvm/sync_check.sh', {
      cwd: PROJECT_ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    })
  } catch (err) {
    return err.stdout || ''
  }
}

const params = loadParams()
const TARGET_URL = `https://${params.target_vm}.iridium.blue`
const CANARY_URL = `${TARGET_URL}${params.canary_app_url_path}`

test.use({ headless: process.env.HEADED !== '1' })

test.describe('Acceptance Run 05 — UI full company-specific ERPNext', () => {
  test.setTimeout(
    (params.wait_budget_seconds + params.topology_convergence_budget_seconds + 900) * 1000
  )

  test('self-check + UI destroy + drag-deploy dev01 — job completes, UI converges, ERPNext canary reachable', async ({ page, browser }) => {
    // ── Step 0: self-check ─
    console.log('[accept-05] self-check: validating harness assumptions')
    let ADMIN_PWD
    try {
      ADMIN_PWD = decryptBuildSecret('erp_user_pwd')
    } catch (err) {
      throw new Error(
        `self-check 0a failed: cannot decrypt ${BUILD_SECRETS_PATH}. ` +
        `Underlying: ${err.message}`
      )
    }
    expect(ADMIN_PWD, 'erp_user_pwd from build_secrets.sops.yml').toBeTruthy()

    const selfSync = runSyncCheck()
    expect(
      selfSync,
      'self-check 0b: sync_check.sh output must contain row markers (✅/❌)'
    ).toMatch(/[✅❌]/)

    const apiResp = await page.request.get(`${API_URL}/api/hosts`)
    expect(apiResp.ok(), 'self-check 0c: Cytoscape API /api/hosts').toBe(true)

    const viteResp = await page.request.get(BASE_URL)
    expect(viteResp.ok(), `self-check 0d: Vite ${BASE_URL}`).toBe(true)

    try {
      execSync(`ssh -o BatchMode=yes -o ConnectTimeout=5 ${params.hypervisor} true`, {
        cwd: PROJECT_ROOT, stdio: ['ignore', 'ignore', 'pipe'],
      })
    } catch (err) {
      throw new Error(`self-check 0e failed: cannot SSH to ${params.hypervisor}: ${err.message}`)
    }

    console.log('[accept-05] self-check OK — proceeding to baseline/destroy')

    // ── Step 1: baseline + destroy via UI (idempotent clean slate) ─
    await page.goto(BASE_URL)
    await waitForGraph(page)

    const baselineResp = await page.request.get(`${API_URL}/api/hosts`)
    const baseline = await baselineResp.json()
    const existing = baseline.hosts.find(h => h.hostname === params.target_vm)
    if (existing) {
      console.log(`[accept-05] ${params.target_vm} present at baseline — destroying via UI`)
      await selectNode(page, params.target_vm)
      await clickInfoButton(page, 'Destroy')
      await page.waitForSelector('#confirm-overlay:not(.hidden)', { timeout: 5_000 })
      const confirmBody = await page.textContent('#confirm-body')
      expect(confirmBody).toContain(params.target_vm)
      await page.click('#confirm-submit')
      await page.waitForSelector('#confirm-overlay', { state: 'hidden', timeout: 10_000 })

      // Wait for destroy job to finish before asserting absence.
      await page.waitForTimeout(3_000)
      const destroyJobsResp = await page.request.get(`${API_URL}/api/jobs`)
      const destroyJobs = await destroyJobsResp.json()
      const [destroyJobId] = Object.entries(destroyJobs).find(
        ([, j]) => j.hostname === params.target_vm && j.status === 'running'
      ) || []
      if (destroyJobId) {
        await waitForJob(page, destroyJobId, 300_000)
      }

      const afterDestroyResp = await page.request.get(`${API_URL}/api/hosts`)
      const afterDestroy = await afterDestroyResp.json()
      const stillThere = afterDestroy.hosts.find(h => h.hostname === params.target_vm)
      expect(stillThere, `${params.target_vm} must be ABSENT after destroy`).toBeFalsy()

      // Rehydrate Cytoscape from post-destroy /api/hosts — bypasses stale 30s poll (#249)
      await page.reload()
      await waitForGraph(page)
    } else {
      console.log(`[accept-05] ${params.target_vm} absent at baseline — nothing to destroy`)
    }

    const onGraphAtBaseline = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(onGraphAtBaseline, `${params.target_vm} must be absent from Cytoscape at baseline`).toBe(false)

    // ── Step 2: UI drag-to-deploy ─
    console.log(`[accept-05] drag tpl-erpnext-restored into Dev zone for ${params.target_vm}`)
    await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) throw new Error('Cytoscape instance not found')
      const tpl = cy.$('#tpl-erpnext-restored')
      if (tpl.empty()) throw new Error('Restored ERPNext template tile not found')
      // Dev zone = right half, top (x > splitX, y < splitY). 600/200 is safely inside.
      tpl.position({ x: 600, y: 200 })
      tpl.emit('dragfree')
    })

    await page.waitForSelector('#dialog-overlay:not(.hidden)', { timeout: 5_000 })

    await page.fill('#f-hostname', params.target_vm)
    await page.fill('#f-nickname', params.target_nickname)
    await page.fill('#f-wg-ip', params.target_wg_ip)
    await page.fill('#f-virbr0-ip', params.target_virbr0_ip)
    await page.fill('#f-hypervisor', params.hypervisor)
    await page.selectOption('#f-backend', params.backend)
    await page.selectOption('#f-zone', params.zone)

    const siteUrl = page.locator('#site-url-preview')
    if (await siteUrl.isVisible()) {
      await expect(siteUrl).toContainText(`${params.target_vm}.iridium.blue`)
    }

    await page.click('#dialog-submit')
    await page.waitForSelector('#dialog-overlay', { state: 'hidden', timeout: 10_000 })

    // ── Step 3: capture provision job id + wait for completion ─
    await page.waitForTimeout(3_000)
    const jobsResp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await jobsResp.json()
    const [jobId] = Object.entries(jobs).find(
      ([, j]) => j.hostname === params.target_vm && j.status === 'running'
    ) || []
    expect(jobId, `provision job for ${params.target_vm} must be running after Deploy submit`).toBeTruthy()

    console.log(`[accept-05] provision job ${jobId} — waiting up to ${params.wait_budget_seconds}s`)
    const startedAt = Date.now()
    await waitForJob(page, jobId, params.wait_budget_seconds * 1000)
    const provisionSeconds = Math.round((Date.now() - startedAt) / 1000)
    console.log(`[accept-05] provision job finished after ${provisionSeconds}s`)

    // ── Step 4: topology convergence ─
    console.log(`[accept-05] awaiting UI convergence within ${params.topology_convergence_budget_seconds}s`)
    const convergenceStart = Date.now()
    await expect(async () => {
      const r = await page.request.get(`${API_URL}/api/hosts`)
      const data = await r.json()
      const h = data.hosts.find(x => x.hostname === params.target_vm)
      expect(h, `${params.target_vm} in /api/hosts`).toBeTruthy()
      expect(h.provisioned, `${params.target_vm} provisioned`).toBe(true)
      expect(h.vm_state, `${params.target_vm} vm_state`).toBe('running')
    }).toPass({
      timeout: params.topology_convergence_budget_seconds * 1000,
      intervals: [5_000],
    })
    const convergenceSeconds = Math.round((Date.now() - convergenceStart) / 1000)
    console.log(`[accept-05] UI converged after ${convergenceSeconds}s`)

    const uiPresent = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(uiPresent, `${params.target_vm} must appear in Cytoscape after convergence`).toBe(true)

    // ── Step 5: ERPNext canary — login + Test Item (parity with Run 02) ─
    console.log(`[accept-05] canary: login as Administrator + GET ${params.canary_app_url_path}`)
    const erp = await browser.newContext()
    try {
      const login = await erp.request.post(`${TARGET_URL}/api/method/login`, {
        form: { usr: 'Administrator', pwd: ADMIN_PWD },
      })
      expect(login.ok(), `ERPNext login (HTTP ${login.status()})`).toBe(true)

      const itemResp = await erp.request.get(
        `${TARGET_URL}/api/resource/${encodeURIComponent(params.canary_doctype)}/${encodeURIComponent(params.canary_name)}`
      )
      expect(
        itemResp.ok(),
        `${params.canary_doctype}/${params.canary_name} REST (HTTP ${itemResp.status()})`
      ).toBe(true)
      const itemBody = await itemResp.json()
      expect(itemBody?.data?.name, 'canary doc name').toBe(params.canary_name)

      const erpPage = await erp.newPage()
      await erpPage.goto(CANARY_URL, { waitUntil: 'networkidle' })
      await expect(erpPage.locator('body')).toContainText(params.canary_name)
    } finally {
      await erp.close()
    }

    // ── Step 6: sync_check — assert specific dev01 row ─
    const syncOut = runSyncCheck()
    expect(
      syncOut,
      `sync_check ERPNext row for ${params.target_vm} must be ✅`
    ).toContain(`✅  ERPNext ${params.target_vm} (${TARGET_URL})`)
  })
})
