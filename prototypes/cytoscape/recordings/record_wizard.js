#!/usr/bin/env node
/**
 * record_wizard.js — Launch Playwright codegen to record the ERPNext setup wizard.
 *
 * Usage:
 *   node recordings/record_wizard.js --url https://dev01.iridium.blue --output recordings/wizard/dev01-20260414.spec.js
 *
 * Opens a headed Chromium with the Playwright Inspector (codegen mode).
 * The user completes the wizard manually. When the browser is closed,
 * the generated test script is saved to the output path.
 *
 * This is the training-exercise entry point for the broader Playwright
 * capture/replay infrastructure (v13-v16 upgrade regression testing).
 */

import { execSync, spawn } from 'child_process'
import { existsSync, mkdirSync } from 'fs'
import { dirname, resolve } from 'path'
import { parseArgs } from 'util'

const { values } = parseArgs({
  options: {
    url:    { type: 'string' },
    output: { type: 'string' },
  },
  strict: true,
})

if (!values.url || !values.output) {
  console.error('Usage: node record_wizard.js --url <url> --output <path>')
  process.exit(2)
}

const outputPath = resolve(values.output)
const outputDir  = dirname(outputPath)

if (!existsSync(outputDir)) {
  mkdirSync(outputDir, { recursive: true })
}

console.log(`Recording wizard at: ${values.url}`)
console.log(`Output will be saved to: ${outputPath}`)
console.log('Close the browser when the wizard is complete.\n')

// Launch Playwright codegen in headed mode.
// --target javascript generates a Playwright test script.
// -o saves the output to the specified file.
const child = spawn('npx', [
  'playwright', 'codegen',
  '--target', 'javascript',
  '-o', outputPath,
  values.url,
], {
  stdio: 'inherit',
  shell: true,
})

child.on('close', (code) => {
  if (code === 0) {
    console.log(`\nRecording saved: ${outputPath}`)
  } else {
    console.error(`\nCodegen exited with code ${code}`)
    process.exit(code)
  }
})
