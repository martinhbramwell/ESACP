#!/usr/bin/env node
/**
 * replay_wizard.js — Replay a previously recorded wizard script.
 *
 * Usage:
 *   node recordings/replay_wizard.js --script recordings/wizard/pseudo-co-wizard.spec.js --url https://dev02.iridium.blue
 *   node recordings/replay_wizard.js --script ... --url ... --config recordings/wizard/alt-config.json
 *
 * Reads the raw Playwright codegen recording, rewrites any hardcoded URLs
 * to the target URL, writes a temporary .cjs copy, and executes it via node.
 *
 * If --config is passed, its JSON contents are forwarded to the child process
 * as WIZARD_CONFIG_JSON — parameterised recordings (#181) read this to
 * override their DEFAULT_CONFIG. Without --config, the recording's default
 * config applies.
 *
 * Exit code 0 on success, non-zero on failure.
 */

import { readFileSync, writeFileSync, unlinkSync, existsSync } from 'fs'
import { spawn } from 'child_process'
import { resolve } from 'path'
import { parseArgs } from 'util'
import { tmpdir } from 'os'
import { join } from 'path'

const { values } = parseArgs({
  options: {
    script: { type: 'string' },
    url:    { type: 'string' },
    config: { type: 'string' },
  },
  strict: true,
})

if (!values.script || !values.url) {
  console.error('Usage: node replay_wizard.js --script <path> --url <url> [--config <json-file>]')
  process.exit(2)
}

const scriptPath = resolve(values.script)
if (!existsSync(scriptPath)) {
  console.error(`Script not found: ${scriptPath}`)
  process.exit(1)
}

const targetUrl = values.url.replace(/\/+$/, '')

// Read the recording and rewrite URLs to point at the target
let code = readFileSync(scriptPath, 'utf-8')

// Extract the original base URL from the first goto() call
const gotoMatch = code.match(/page\.goto\(['"]([^'"]+)['"]\)/)
if (gotoMatch) {
  const originalUrl = new URL(gotoMatch[1])
  const originalBase = `${originalUrl.protocol}//${originalUrl.host}`
  code = code.replaceAll(originalBase, targetUrl)
}

// Force headless mode for automated replay
code = code.replace(/headless:\s*false/, 'headless: true')

// Write as .cjs inside the project tree so Node resolves playwright from node_modules.
const projectDir = resolve(scriptPath, '..', '..', '..')
const tmpScript = join(projectDir, `pw-replay-${Date.now()}.cjs`)
writeFileSync(tmpScript, code)

console.log(`Replaying: ${scriptPath}`)
console.log(`Against:   ${targetUrl}`)

const msPlaywrightPath = join(process.env.HOME || '', '.cache', 'ms-playwright')
const childEnv = { ...process.env, PLAYWRIGHT_BROWSERS_PATH: msPlaywrightPath }

if (values.config) {
  const configPath = resolve(values.config)
  if (!existsSync(configPath)) {
    console.error(`Config file not found: ${configPath}`)
    process.exit(1)
  }
  const configRaw = readFileSync(configPath, 'utf-8')
  // Validate JSON before passing through so a bad file fails loudly here rather
  // than inside the child process.
  try { JSON.parse(configRaw) } catch (err) {
    console.error(`Config file is not valid JSON (${configPath}): ${err.message}`)
    process.exit(1)
  }
  childEnv.WIZARD_CONFIG_JSON = configRaw
  console.log(`Config:    ${configPath}`)
}

const child = spawn('node', [tmpScript], {
  stdio: 'inherit',
  cwd: projectDir,
  env: childEnv,
})

child.on('close', (code) => {
  try { unlinkSync(tmpScript) } catch { /* ignore */ }

  if (code === 0) {
    console.log('\nReplay completed successfully.')
  } else {
    console.error(`\nReplay failed (exit code ${code})`)
    process.exit(code)
  }
})
