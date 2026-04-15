// api.js — fetch helpers for the ESACP Control Plane API (tools/api.py)
//
// All calls go through Vite's /api proxy → localhost:8088.
// Each function throws on network error or non-2xx response.

const TIMEOUT_MS = 5000

function signal() {
  return AbortSignal.timeout(TIMEOUT_MS)
}

async function post(path, body) {
  const res = await fetch(path, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
    signal:  signal(),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`)
  return data
}

// Returns { hosts: [...], suggestions: { wg_ip, virbr0_ip } }
export async function fetchHosts() {
  const res = await fetch('/api/hosts', { signal: signal() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Returns { ok: true, hostname }
export async function addHost({ hostname, nickname, virbr0_ip, wg_ip, backend = 'kvm', hypervisor = 'toshiba', zone = 'development', vm_role = 'dev' }) {
  return post('/api/hosts/add', { hostname, nickname, virbr0_ip, wg_ip, backend, hypervisor, zone, vm_role })
}

// Returns { job_id: { status, hostname }, ... }
export async function fetchJobs() {
  const res = await fetch('/api/jobs', { signal: signal() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Returns { job_id }
export async function startDestroy(hostname) {
  return post(`/api/destroy/${hostname}`, {})
}

// Returns { job_id, hostname } — registers host AND starts template-based provision job atomically
// nickname: Frappe bench suffix, e.g. "D1IRBL" → bench dir "frappe-bench-D1IRBL"
// zone determines domain: development/staging → iridium.blue, production → logichem.solutions
export async function startProvisionErpnext({ hostname, nickname, virbr0_ip, wg_ip, hypervisor = 'toshiba', zone = 'development', vm_role = 'dev:unspecified' }) {
  return post('/api/provision/erpnext', { hostname, nickname, virbr0_ip, wg_ip, hypervisor, zone, vm_role })
}

// Returns { job_id, hostname } — generic ERPNext (no prod data) + wizard completion
export async function startProvisionErpnextGeneric({ hostname, nickname, virbr0_ip, wg_ip, hypervisor = 'toshiba', zone = 'development', vm_role = 'dev:unspecified', wizard_mode = 'record', wizard_arg = '' }) {
  return post('/api/provision/erpnext-generic', { hostname, nickname, virbr0_ip, wg_ip, hypervisor, zone, vm_role, wizard_mode, wizard_arg })
}

// Returns { recordings: [{ name, size_kb, created_at }] }
export async function fetchWizardRecordings() {
  const res = await fetch('/api/wizard/recordings', { signal: signal() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Returns { backups: [{ filename, size_mb, created_at }] }
export async function fetchWizardBackups() {
  const res = await fetch('/api/wizard/backups', { signal: signal() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Returns { image, built_at, frappe_branch, erpnext_branch, state }
export async function fetchTemplateStatus() {
  const res = await fetch('/api/template/status', { signal: signal() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Returns { job_id }
export async function startBuildTemplate() {
  return post('/api/build/template', {})
}

// Returns { ok: true }
export async function deleteTemplate() {
  const res = await fetch('/api/template', { method: 'DELETE', signal: signal() })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`)
  return data
}

// Returns { job_id }
export async function startRefresh(hostname) {
  return post(`/api/refresh/${hostname}`, {})
}

// VM power control — returns { ok, message } or throws with detail
export async function startVm(hostname) {
  return post(`/api/vm/${hostname}/start`, {})
}

export async function stopVm(hostname) {
  return post(`/api/vm/${hostname}/stop`, {})
}

export async function rebootVm(hostname) {
  return post(`/api/vm/${hostname}/reboot`, {})
}

// Returns { web, app, db } each 'green' | 'amber' | 'red'
export async function fetchHealth(hostname) {
  const res = await fetch(`/api/health/${hostname}`, { signal: signal() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Poll a job every intervalMs until it reaches a terminal state.
// onLines(newLines[])  — called whenever new log lines arrive
// onDone(status)       — called once with 'done' or 'error' when the job ends
export function pollJob(jobId, onLines, onDone, intervalMs = 1500) {
  let seen = 0

  const id = setInterval(async () => {
    try {
      const res = await fetch(`/api/jobs/${jobId}`)
      if (!res.ok) { clearInterval(id); onDone('error'); return }

      const job      = await res.json()
      const newLines = job.log.slice(seen)
      if (newLines.length) {
        onLines(newLines)
        seen = job.log.length
      }

      if (job.status !== 'running') {
        clearInterval(id)
        onDone(job.status)
      }
    } catch {
      clearInterval(id)
      onDone('error')
    }
  }, intervalMs)

  // Return a cancel handle
  return () => clearInterval(id)
}
