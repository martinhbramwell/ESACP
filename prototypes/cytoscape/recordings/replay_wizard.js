#!/usr/bin/env node
/**
 * replay_wizard.js — Replay a previously recorded wizard script.
 *
 * Usage:
 *   node recordings/replay_wizard.js --script recordings/wizard/dev01-20260414.spec.js --url https://dev02.iridium.blue
 *
 * Runs the recorded Playwright script against a different target URL.
 * The script is executed via npx playwright test with the --config
 * pointed at a minimal inline config that overrides baseURL.
 *
 * Exit code 0 on success, non-zero on failure.
 */

import { writeFileSync, unlinkSync, existsSync } from 'fs'
import { spawn } from 'child_process'
import { resolve, dirname } from 'path'
import { parseArgs } from 'util'
import { tmpdir } from 'os'
import { join } from 'path'

const { values } = parseArgs({
  options: {
    script: { type: 'string' },
    url:    { type: 'string' },
  },
  strict: true,
})

if (!values.script || !values.url) {
  console.error('Usage: node replay_wizard.js --script <path> --url <url>')
  process.exit(2)
}

const scriptPath = resolve(values.script)
if (!existsSync(scriptPath)) {
  console.error(`Script not found: ${scriptPath}`)
  process.exit(1)
}

// Create a temporary Playwright config that overrides baseURL
// and points testDir at the recording's directory.
const tmpConfig = join(tmpdir(), `pw-replay-${Date.now()}.config.js`)
const configContent = `
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: '${dirname(scriptPath)}',
  testMatch: '${scriptPath.split('/').pop()}',
  timeout: 600_000,
  use: {
    baseURL: '${values.url}',
    headless: false,
    ignoreHTTPSErrors: true,
  },
  retries: 0,
  workers: 1,
});
`
writeFileSync(tmpConfig, configContent)

console.log(`Replaying: ${scriptPath}`)
console.log(`Against:   ${values.url}`)

const child = spawn('npx', [
  'playwright', 'test',
  '--config', tmpConfig,
], {
  stdio: 'inherit',
  shell: true,
  cwd: resolve(dirname(scriptPath), '..', '..'),
})

child.on('close', (code) => {
  // Clean up temp config
  try { unlinkSync(tmpConfig) } catch { /* ignore */ }

  if (code === 0) {
    console.log('\nReplay completed successfully.')
  } else {
    console.error(`\nReplay failed (exit code ${code})`)
    process.exit(code)
  }
})
