// @ts-check
import { test, expect } from '@playwright/test'
import { spawn, execSync } from 'node:child_process'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { BASE_URL, API_URL, waitForGraph } from './helpers.js'

/**
 * Acceptance Run 04 — CLI dev VM, skeletal ERPNext restored from B03.
 *
 * Three-step CLI lifecycle:
 *   1. destroy-as-precondition if dev01 present (Run 03 exit state)
 *   2. ./tools/esacp.py addHost dev01 ...
 *   3. ./tools/esacp.py provisionGeneric dev01 --wizard-mode existing
 *                         --wizard-arg <B03 backup basename>
 *
 * "existing" mode restores the named .tgz from platforms/kvm/golden_backups/
 * via handleRestore.sh during stage 7 — no wizard replay, no new backup
 * captured. Run 04's acceptance is that the Pseudo-Co canary facts from
 * Run 03 reappear in the restored instance.
 *
 * Plan:    ~/.claude/plans/acceptance-matrix-transport-parity.md
 * Agenda:  docs/SessionLogs/acceptance-matrix/04-cli-vm-pseudo-company-restore-from-wizard-backup.md
 * Params:  docs/SessionLogs/acceptance-matrix/params/04-cli-pseudo-restore.yml
 *
 * Parity partner: Run 07 (UI-driven restore from B06).
 */

const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)
const PROJECT_ROOT = path.resolve(__dirname, '../../..')
const PARAM_PATH = path.join(
  PROJECT_ROOT,
  'docs/SessionLogs/acceptance-matrix/params/04-cli-pseudo-restore.yml'
)
const BUILD_SECRETS_PATH = path.join(PROJECT_ROOT, 'config/build_secrets.sops.yml')
const GOLDEN_BACKUPS_DIR = path.join(PROJECT_ROOT, 'platforms/kvm/golden_backups')

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
  // sync_check.sh exits non-zero when ANY row fails — including pre-existing
  // idle-VM ping failures unrelated to dev01 (#247). Swallow, inspect stdout.
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

test.describe('Acceptance Run 04 — CLI restore skeletal ERPNext from B03', () => {
  test.setTimeout(
    (params.wait_budget_seconds + params.topology_convergence_budget_seconds + 900) * 1000
  )

  test('self-check + destroy + addHost + provisionGeneric existing dev01 — exit 0, UI converges, Pseudo-Co canary from B03, no new backup', async ({ page, browser }) => {
    // ── Step 0: self-check — validate harness assumptions BEFORE SUT spend ─
    console.log('[accept-04] self-check: validating harness assumptions')

    // 0a. sops decrypt of build_secrets → ERP_ADMIN_PWD derivable
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

    // 0e. toshiba SSH reachable (destroy + provisionGeneric depend on it)
    try {
      execSync(`ssh -o BatchMode=yes -o ConnectTimeout=5 ${params.hypervisor} true`, {
        cwd: PROJECT_ROOT, stdio: ['ignore', 'ignore', 'pipe'],
      })
    } catch (err) {
      throw new Error(`self-check 0e failed: cannot SSH to ${params.hypervisor}: ${err.message}`)
    }

    // 0f. B03 backup file exists at the path --wizard-arg will resolve to
    const backupPath = path.join(GOLDEN_BACKUPS_DIR, params.backup_source)
    try {
      statSync(backupPath)
    } catch {
      throw new Error(`self-check 0f failed: B03 backup not found: ${backupPath}`)
    }

    console.log('[accept-04] self-check OK — proceeding to baseline/destroy')

    // ── Step 1: baseline + destroy-as-precondition (idempotent clean slate) ─
    await page.goto(BASE_URL)
    await waitForGraph(page)

    const baselineResp = await page.request.get(`${API_URL}/api/hosts`)
    const baseline = await baselineResp.json()
    const existing = baseline.hosts.find(h => h.hostname === params.target_vm)
    if (existing) {
      console.log(`[accept-04] ${params.target_vm} present at baseline — destroying (Run 03 exit-state)`)
      execSync(`echo y | ./tools/esacp.py destroy ${params.target_vm}`, {
        cwd: PROJECT_ROOT, stdio: ['ignore', 'inherit', 'inherit'],
        shell: '/bin/bash',
      })
      const afterDestroyResp = await page.request.get(`${API_URL}/api/hosts`)
      const afterDestroy = await afterDestroyResp.json()
      const stillThere = afterDestroy.hosts.find(h => h.hostname === params.target_vm)
      expect(stillThere, `${params.target_vm} must be ABSENT after destroy`).toBeFalsy()

      // Rehydrate Cytoscape from post-destroy /api/hosts — the 30s poll tick
      // may not have fired yet, so the in-memory graph is otherwise stale (#249).
      await page.reload()
      await waitForGraph(page)
    } else {
      console.log(`[accept-04] ${params.target_vm} absent at baseline — nothing to destroy`)
    }

    const onGraphAtBaseline = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(onGraphAtBaseline, `${params.target_vm} must be absent from Cytoscape at baseline`).toBe(false)

    // Snapshot golden_backups/ BEFORE build — restore must NOT add a new one.
    const backupsBefore = new Set(listGoldenBackups().map(b => b.name))
    console.log(`[accept-04] golden_backups baseline: ${backupsBefore.size} file(s)`)
    expect(
      backupsBefore.has(params.backup_source),
      `B03 (${params.backup_source}) must be present before restore`,
    ).toBe(true)

    // ── Step 2: addHost (registration only — no VM build) ──────────────────
    console.log(`[accept-04] addHost ${params.target_vm}`)
    execSync(
      `./tools/esacp.py addHost ${params.target_vm} ` +
      `--zone ${params.zone} ` +
      `--vm-role ${params.vm_role} ` +
      `--hypervisor ${params.hypervisor}`,
      { cwd: PROJECT_ROOT, stdio: ['ignore', 'inherit', 'inherit'] }
    )

    const afterAddResp = await page.request.get(`${API_URL}/api/hosts`)
    const afterAdd = await afterAddResp.json()
    const registered = afterAdd.hosts.find(h => h.hostname === params.target_vm)
    expect(registered, `${params.target_vm} must be present after addHost`).toBeTruthy()
    expect(registered.provisioned, `${params.target_vm} provisioned should be false pre-build`).toBe(false)

    // ── Step 3: provisionGeneric existing (stages 1-9 + restore from B03) ──
    console.log(
      `[accept-04] provisionGeneric ${params.target_vm} existing ${params.backup_source}  ` +
      `(wait budget: ${params.wait_budget_seconds}s)`
    )
    const startedAt = Date.now()
    const proc = spawn(
      './tools/esacp.py',
      ['provisionGeneric', params.target_vm,
       '--wizard-mode', 'existing',
       '--wizard-arg', params.backup_source],
      {
        cwd: PROJECT_ROOT,
        stdio: ['ignore', 'pipe', 'pipe'],
        env: { ...process.env },
      },
    )
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
        reject(new Error(`provisionGeneric exceeded wait_budget_seconds=${params.wait_budget_seconds}`))
      }, params.wait_budget_seconds * 1000)
      proc.on('exit', code => { clearTimeout(timer); resolve(code) })
      proc.on('error', err => { clearTimeout(timer); reject(err) })
    })
    const provisionSeconds = Math.round((Date.now() - startedAt) / 1000)
    console.log(`[accept-04] provisionGeneric exited code=${exitCode} after ${provisionSeconds}s`)
    expect(exitCode, `provisionGeneric exit (stderr tail: ${stderrTail})`).toBe(0)

    // ── Step 4: topology convergence ───────────────────────────────────────
    console.log(`[accept-04] awaiting UI convergence within ${params.topology_convergence_budget_seconds}s`)
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
    console.log(`[accept-04] UI converged after ${convergenceSeconds}s`)

    const uiPresent = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(uiPresent, `${params.target_vm} must appear in Cytoscape after convergence`).toBe(true)

    // ── Step 5: post-restore canary — Pseudo-Co reappears from B03 ─────────
    console.log(`[accept-04] canary: login + verify Company ${params.company_name} (restored from B03)`)
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

      // Exactly 1 Company = skeletal restore (B03 was wizard-only, no extras).
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

    // ── Step 6: golden_backups delta = 0 (restore must NOT add a backup) ───
    const backupsAfter = listGoldenBackups()
    const newBackups = backupsAfter.filter(b => !backupsBefore.has(b.name))
    expect(
      newBackups.length,
      `restore must NOT produce a new backup, got ${newBackups.length} new: ${newBackups.map(b => b.name).join(', ')}`,
    ).toBe(0)
    expect(
      backupsAfter.some(b => b.name === params.backup_source),
      `B03 (${params.backup_source}) must still be present after restore`,
    ).toBe(true)

    // ── Step 7: sync_check — assert specific dev01 row (#247) ──────────────
    const syncOut = runSyncCheck()
    expect(
      syncOut,
      `sync_check ERPNext row for ${params.target_vm} must be ✅`,
    ).toContain(`✅  ERPNext ${params.target_vm} (${TARGET_URL})`)
  })
})
