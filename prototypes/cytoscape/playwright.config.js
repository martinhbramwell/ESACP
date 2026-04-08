import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 2_400_000,      // 40 min — rebuild = destroy (~2 min) + deploy (~30 min) + margin
  expect: { timeout: 10_000 },
  retries: 0,              // no retries — infra ops are not idempotent
  workers: 1,              // serial — shared hypervisor
  use: {
    baseURL: 'http://localhost:5173',
    headless: false,        // watch it work
    viewport: { width: 1280, height: 900 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
})
