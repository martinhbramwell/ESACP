// helpers.js — shared Playwright utilities for ESACP topology tests

export const BASE_URL = process.env.TOPOLOGY_URL || 'http://localhost:5173'
export const API_URL  = process.env.API_URL || 'http://localhost:8088'

export async function waitForGraph(page) {
  await page.waitForSelector('#cy canvas', { timeout: 10_000 })
  await page.waitForTimeout(1500)
}

export async function selectNode(page, hostname) {
  await page.evaluate((h) => {
    const cy = document.querySelector('#cy')?._cyreg?.cy
    if (!cy) throw new Error('Cytoscape instance not found')
    const node = cy.$(`#${h}`)
    if (node.empty()) throw new Error(`Node '${h}' not found on graph`)
    node.emit('tap')
  }, hostname)
  await page.waitForTimeout(500)
}

export async function clickInfoButton(page, buttonText) {
  const btn = page.locator('#info-panel button', { hasText: buttonText })
  await btn.waitFor({ state: 'visible', timeout: 5_000 })
  await btn.click()
}

// Job status contract — see tools/job_worker.py:84,86,88 and tools/api/jobs.py:53
//   'running' — non-terminal (default when status file absent)
//   'done'    — success (job_worker exit 0)
//   'error'   — failure (exception raised OR unknown job type)
// Any other value is treated as unexpected and fails fast on the next poll.
export async function waitForJob(page, jobId, timeoutMs = 2_100_000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const resp = await page.request.get(`${API_URL}/api/jobs`)
    const jobs = await resp.json()
    const job = jobs[jobId]
    if (!job) throw new Error(`Job ${jobId} not found`)
    if (job.status === 'done')  return job
    if (job.status === 'error') throw new Error(`Job ${jobId} errored`)
    if (job.status !== 'running') throw new Error(`Job ${jobId} unexpected status '${job.status}'`)
    await page.waitForTimeout(5_000)
  }
  throw new Error(`Job ${jobId} timed out after ${timeoutMs}ms`)
}
