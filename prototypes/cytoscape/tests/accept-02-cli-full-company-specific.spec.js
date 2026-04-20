// @ts-check
import { test, expect } from '@playwright/test'
import { spawn, execSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { BASE_URL, API_URL, waitForGraph } from './helpers.js'

/**
 * Acceptance Run 02 — CLI dev VM, full company-specific ERPNext from golden production backup.
 *
 * Two-step CLI lifecycle (per shelved-attempt-3 decisions D1=(a), D2=(a)):
 *   1. ./tools/esacp.py addHost dev01 ...
 *   2. ./tools/esacp.py provision dev01     (Config.provision_mode defaults to "restored")
 *
 * Plan:    ~/.claude/plans/acceptance-matrix-transport-parity.md
 * Agenda:  docs/SessionLogs/acceptance-matrix/02-cli-vm-full-logichem-from-backup.md
 *          (filename frozen pending #246; new artifacts use company-specific token)
 * Params:  docs/SessionLogs/acceptance-matrix/params/02-cli-full-company-specific.yml
 *
 * Parity partner: Run 05 (UI-driven full company-specific restore). Same canary asserted.
 *
 * Administrator password: derived automatically from config/build_secrets.sops.yml
 * (field erp_user_pwd). The provisioning pipeline resets Administrator to that value
 * post-restore — see memory/feedback_lab_admin_password.md for the why.
 */

const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)
const PROJECT_ROOT = path.resolve(__dirname, '../../..')
const PARAM_PATH = path.join(
  PROJECT_ROOT,
  'docs/SessionLogs/acceptance-matrix/params/02-cli-full-company-specific.yml'
)
const BUILD_SECRETS_PATH = path.join(PROJECT_ROOT, 'config/build_secrets.sops.yml')

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
  // idle-VM ping failures that are unrelated to the host under test (#247).
  // Swallow exit status; inspect stdout.
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

test.describe('Acceptance Run 02 — CLI full company-specific ERPNext', () => {
  // wait_budget (provision) + convergence + 15 min margin (self-check + destroy + canary + sync_check)
  test.setTimeout(
    (params.wait_budget_seconds + params.topology_convergence_budget_seconds + 900) * 1000
  )

  test('self-check + destroy + addHost + provision dev01 — exit 0, UI converges, ERPNext canary reachable', async ({ page, browser }) => {
    // ── Step 0: self-check — validate test-harness assumptions BEFORE any SUT spend ─
    console.log('[accept-02] self-check: validating harness assumptions')

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

    // 0b. sync_check.sh parseable via try/catch path (#247 regression guard)
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

    // 0e. toshiba SSH reachable (destroy depends on it)
    try {
      execSync(`ssh -o BatchMode=yes -o ConnectTimeout=5 ${params.hypervisor} true`, {
        cwd: PROJECT_ROOT, stdio: ['ignore', 'ignore', 'pipe'],
      })
    } catch (err) {
      throw new Error(`self-check 0e failed: cannot SSH to ${params.hypervisor}: ${err.message}`)
    }

    console.log('[accept-02] self-check OK — proceeding to baseline/destroy')

    // ── Step 1: baseline + destroy-as-precondition (idempotent clean slate) ─
    await page.goto(BASE_URL)
    await waitForGraph(page)

    const baselineResp = await page.request.get(`${API_URL}/api/hosts`)
    const baseline = await baselineResp.json()
    const existing = baseline.hosts.find(h => h.hostname === params.target_vm)
    if (existing) {
      console.log(`[accept-02] ${params.target_vm} present at baseline — destroying (attempt-restart safety)`)
      execSync(`echo y | ./tools/esacp.py destroy ${params.target_vm}`, {
        cwd: PROJECT_ROOT, stdio: ['ignore', 'inherit', 'inherit'],
        shell: '/bin/bash',
      })
      const afterDestroyResp = await page.request.get(`${API_URL}/api/hosts`)
      const afterDestroy = await afterDestroyResp.json()
      const stillThere = afterDestroy.hosts.find(h => h.hostname === params.target_vm)
      expect(stillThere, `${params.target_vm} must be ABSENT after destroy`).toBeFalsy()
    } else {
      console.log(`[accept-02] ${params.target_vm} absent at baseline — nothing to destroy`)
    }

    const onGraphAtBaseline = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(onGraphAtBaseline, `${params.target_vm} must be absent from Cytoscape at baseline`).toBe(false)

    // ── Step 2: addHost (registration only — no VM build) ──────────────────
    console.log(`[accept-02] addHost ${params.target_vm}`)
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

    // ── Step 3: provision (full restore from golden production backup) ─────
    console.log(
      `[accept-02] provision ${params.target_vm}  ` +
      `(wait budget: ${params.wait_budget_seconds}s)`
    )
    const startedAt = Date.now()
    const proc = spawn('./tools/esacp.py', ['provision', params.target_vm], {
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
        reject(new Error(`provision exceeded wait_budget_seconds=${params.wait_budget_seconds}`))
      }, params.wait_budget_seconds * 1000)
      proc.on('exit', code => { clearTimeout(timer); resolve(code) })
      proc.on('error', err => { clearTimeout(timer); reject(err) })
    })
    const provisionSeconds = Math.round((Date.now() - startedAt) / 1000)
    console.log(`[accept-02] provision exited code=${exitCode} after ${provisionSeconds}s`)
    expect(exitCode, `provision exit (stderr tail: ${stderrTail})`).toBe(0)

    // ── Step 4: topology convergence ───────────────────────────────────────
    console.log(`[accept-02] awaiting UI convergence within ${params.topology_convergence_budget_seconds}s`)
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
    console.log(`[accept-02] UI converged after ${convergenceSeconds}s`)

    const uiPresent = await page.evaluate((h) => {
      const cy = document.querySelector('#cy')?._cyreg?.cy
      return cy ? !cy.$(`#${h}`).empty() : false
    }, params.target_vm)
    expect(uiPresent, `${params.target_vm} must appear in Cytoscape after convergence`).toBe(true)

    // ── Step 5: ERPNext canary — login + Test Item ─────────────────────────
    console.log(`[accept-02] canary: login as Administrator + GET ${params.canary_app_url_path}`)
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

    // ── Step 6: sync_check — assert specific dev01 row (#247) ──────────────
    const syncOut = runSyncCheck()
    expect(
      syncOut,
      `sync_check ERPNext row for ${params.target_vm} must be ✅`
    ).toContain(`✅  ERPNext ${params.target_vm} (${TARGET_URL})`)
  })
})
