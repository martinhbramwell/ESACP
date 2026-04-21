// @ts-check
import { test, expect } from '@playwright/test'
import { execSync } from 'node:child_process'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { BASE_URL, API_URL, waitForGraph, selectNode, clickInfoButton, waitForJob } from './helpers.js'

/**
 * Acceptance Run 07 — UI dev VM, skeletal ERPNext restored from B06 (wizard backup).
 *
 * Final matrix run. Parity partner: Run 04 (CLI pseudo_restore from B03).
 *
 * UI drag-to-deploy lifecycle:
 *   1. Destroy existing dev01 via Cytoscape right-click.
 *   2. Drag tpl-erpnext-generic into Dev zone → Deploy Generic ERPNext dialog.
 *   3. Fill hostname/nickname/IPs/hypervisor/zone, select wizard_mode=existing,
 *      choose B06 tarball from dropdown, submit → waitForJob.
 *   4. Assert Pseudo-Co canary (verbatim parity with Run 04 Step 5).
 *   5. Assert golden-backups delta == 0 — restore must NOT produce a new backup.
 *   6. Assert sync_check ERPNext dev01 row is ✅.
 *
 * Plan:    ~/.claude/plans/acceptance-matrix-transport-parity.md
 * Agenda:  docs/SessionLogs/acceptance-matrix/07-ui-vm-pseudo-company-restore-from-wizard-backup.md
 * Params:  docs/SessionLogs/acceptance-matrix/params/07-ui-pseudo-restore.yml
 *
 * Administrator password: derived from config/build_secrets.sops.yml (erp_user_pwd).
 */

const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)
const PROJECT_ROOT = path.resolve(__dirname, '../../..')
const PARAM_PATH = path.join(
  PROJECT_ROOT,
  'docs/SessionLogs/acceptance-matrix/params/07-ui-pseudo-restore.yml'
)
const BUILD_SECRETS_PATH = path.join(PROJECT_ROOT, 'config/build_secrets.sops.yml')
const GOLDEN_BACKUPS_DIR = path.join(PROJECT_ROOT, 'platforms/kvm/golden_backups')

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

function listGoldenBackups() {
  try {
    return readdirSync(GOLDEN_BACKUPS_DIR)
      .filter(n => n.endsWith('.tgz'))
      .map(n => ({ name: n, mtime: statSync(path.join(GOLDEN_BACKUPS_DIR, n)).mtimeMs }))
  } catch {
    return []
  }
}

const params = loadParams()
const TARGET_URL = `https://${params.target_vm}.iridium.blue`

test.use({ headless: process.env.HEADED !== '1' })

test.describe('Acceptance Run 07 — UI pseudo-restore skeletal ERPNext from B06', () => {
  test.setTimeout(
    (params.wait_budget_seconds + params.topology_convergence_budget_seconds + 900) * 1000
  )

  test('self-check + UI destroy + drag-deploy generic existing dev01 — job completes, UI converges, Pseudo-Co canary from B06, no new backup', async ({ page, browser }) => {
    // ── Step 0: self-check — validate harness assumptions BEFORE SUT spend ─
    console.log('[accept-07] self-check: validating harness assumptions')

    // 0a. sops decrypt of build_secrets → ADMIN_PWD derivable
    let ADMIN_PWD
    try {
      ADMIN_PWD = decryptBuildSecret('erp_user_pwd')
    } catch (err) {
      throw new Error(
        `self-check 0a failed: cannot decrypt ${BUILD_SECRETS_PATH}. ` +
        `Verify sops + age key. Underlying: ${err.message}`
      )
    }
    expect(ADMIN_PWD, 'erp_user_pwd from build_secrets.sops.yml').toBeTruthy()

    // 0b. sync_check.sh parseable (#247 regression guard)
    const selfSync = runSyncCheck()
    expect(
      selfSync,
      'self-check 0b: sync_check.sh output must contain row markers (✅/❌)'
    ).toMatch(/[✅❌]/)

    // 0c. Cytoscape API :8088 reachable
    const apiResp = await page.request.get(`${API_URL}/api/hosts`)
    expect(apiResp.ok(), 'self-check 0c: Cytoscape API /api/hosts').toBe(true)

    // 0d. Vite :5173 reachable
    const viteResp = await page.request.get(BASE_URL)
    expect(viteResp.ok(), `self-check 0d: Vite ${BASE_URL}`).toBe(true)

    // 0e. toshiba SSH reachable (destroy + provision depend on it)
    try {
      execSync(`ssh -o BatchMode=yes -o ConnectTimeout=5 ${params.hypervisor} true`, {
        cwd: PROJECT_ROOT, stdio: ['ignore', 'ignore', 'pipe'],
      })
    } catch (err) {
      throw new Error(`self-check 0e failed: cannot SSH to ${params.hypervisor}: ${err.message}`)
    }

    // 0f. B06 backup file exists at the path the UI dropdown will resolve to
    const backupPath = path.join(GOLDEN_BACKUPS_DIR, params.backup_source)
    try {
      statSync(backupPath)
    } catch {
      throw new Error(`self-check 0f failed: B06 backup not found: ${backupPath}`)
    }

    console.log('[accept-07] self-check OK — proceeding to baseline/destroy')

    // ── Step 1: baseline + destroy via UI (idempotent clean slate) ─
    await page.goto(BASE_URL)
    await waitForGraph(page)

    const baselineResp = await page.request.get(`${API_URL}/api/hosts`)
    const baseline = await baselineResp.json()
    const existing = baseline.hosts.find(h => h.hostname === params.target_vm)
    if (existing) {
      console.log(`[accept-07] ${params.target_vm} present at baseline — destroying via UI`)
      await selectNode(page, params.target_vm)
      await clickInfoButton(page, 'Destroy')
      await page.waitForSelector('#confirm-overlay:not(.hidden)', { timeout: 5_000 })
      const confirmBody = await page.textContent('#confirm-body')
      expect(confirmBody).toContain(params.target_vm)
      await page.click('#confirm-submit')
      await page.waitForSelector('#confirm-overlay', { state: 'hidden', timeout: 10_000 })

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
      console.log(`[accept-07] ${params.target_vm} absent at baseline — nothing to destroy`)
    }

    const onGraphAtBaseline = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(onGraphAtBaseline, `${params.target_vm} must be absent from Cytoscape at baseline`).toBe(false)

    // Snapshot golden_backups/ BEFORE build — restore must NOT add a new one.
    const backupsBefore = new Set(listGoldenBackups().map(b => b.name))
    console.log(`[accept-07] golden_backups baseline: ${backupsBefore.size} file(s)`)
    expect(
      backupsBefore.has(params.backup_source),
      `B06 (${params.backup_source}) must be present before restore`,
    ).toBe(true)

    // ── Step 2: UI drag-to-deploy (Generic ERPNext + existing wizard backup) ─
    console.log(`[accept-07] drag tpl-erpnext-generic into Dev zone for ${params.target_vm}`)
    await page.evaluate(() => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      if (!cy) throw new Error('Cytoscape instance not found')
      const tpl = cy.$('#tpl-erpnext-generic')
      if (tpl.empty()) throw new Error('Generic ERPNext template tile not found')
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

    // Wizard mode: existing (restore from B06 — main.js:1791,1843)
    await page.click(`input[name="wizard_mode"][value="${params.wizard_mode}"]`)
    await page.waitForSelector('#wizard-existing-select:not([style*="display: none"])', { timeout: 3_000 })
    await page.selectOption('#f-wizard-backup', params.backup_source)

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

    console.log(`[accept-07] provision job ${jobId} — waiting up to ${params.wait_budget_seconds}s`)
    const startedAt = Date.now()
    await waitForJob(page, jobId, params.wait_budget_seconds * 1000)
    const provisionSeconds = Math.round((Date.now() - startedAt) / 1000)
    console.log(`[accept-07] provision job finished after ${provisionSeconds}s`)

    // ── Step 4: topology convergence ─
    console.log(`[accept-07] awaiting UI convergence within ${params.topology_convergence_budget_seconds}s`)
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
    console.log(`[accept-07] UI converged after ${convergenceSeconds}s`)

    const uiPresent = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(uiPresent, `${params.target_vm} must appear in Cytoscape after convergence`).toBe(true)

    // ── Step 5: post-restore canary — Pseudo-Co reappears from B06 ─
    //           (VERBATIM parity with accept-04 Step 5)
    console.log(`[accept-07] canary: login + verify Company ${params.company_name} (restored from B06)`)
    const erp = await browser.newContext()
    try {
      const login = await erp.request.post(`${TARGET_URL}/api/method/login`, {
        form: { usr: 'Administrator', pwd: ADMIN_PWD },
      })
      expect(login.ok(), `ERPNext login (HTTP ${login.status()})`).toBe(true)

      const companyResp = await erp.request.get(
        `${TARGET_URL}/api/resource/Company/${encodeURIComponent(params.company_name)}`,
      )
      expect(
        companyResp.ok(),
        `Company/${params.company_name} REST (HTTP ${companyResp.status()})`,
      ).toBe(true)
      const companyBody = await companyResp.json()
      expect(companyBody?.data?.name, 'Company.name').toBe(params.company_name)
      expect(companyBody?.data?.abbr, 'Company.abbr').toBe(params.company_abbr)
      expect(companyBody?.data?.default_currency, 'Company.default_currency').toBe(params.company_currency)
      expect(companyBody?.data?.country, 'Company.country').toBe(params.company_country)

      // Exactly 1 Company = skeletal restore (B06 was wizard-only, no extras).
      const countResp = await erp.request.get(
        `${TARGET_URL}/api/method/frappe.client.get_count?doctype=Company`,
      )
      expect(countResp.ok(), 'Company count REST').toBe(true)
      const countBody = await countResp.json()
      expect(
        countBody?.message,
        `exactly 1 Company record expected (skeletal restore), got ${countBody?.message}`,
      ).toBe(1)
    } finally {
      await erp.close()
    }

    // ── Step 6: golden_backups delta = 0 (restore must NOT add a backup) ─
    //           (VERBATIM parity with accept-04 Step 6)
    const backupsAfter = listGoldenBackups()
    const newBackups = backupsAfter.filter(b => !backupsBefore.has(b.name))
    expect(
      newBackups.length,
      `restore must NOT produce a new backup, got ${newBackups.length} new: ${newBackups.map(b => b.name).join(', ')}`,
    ).toBe(0)
    expect(
      backupsAfter.some(b => b.name === params.backup_source),
      `B06 (${params.backup_source}) must still be present after restore`,
    ).toBe(true)

    // ── Step 7: sync_check — assert specific dev01 row (#247) ─
    const syncOut = runSyncCheck()
    expect(
      syncOut,
      `sync_check ERPNext row for ${params.target_vm} must be ✅`,
    ).toContain(`✅  ERPNext ${params.target_vm} (${TARGET_URL})`)
  })
})
