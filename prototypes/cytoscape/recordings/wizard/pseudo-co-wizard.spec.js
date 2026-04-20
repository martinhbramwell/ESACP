const { chromium } = require('playwright');

// Pseudo-Co setup wizard — reusable recording for acceptance Run 03 (CLI) and
// Run 06 (UI). replay_wizard.js rewrites the base URL per target VM at replay
// time, so the hardcoded dev01 URL below is a template only.
//
// Administrator password is the dev-lab value sourced from
// config/build_secrets.sops.yml (erp_user_pwd="sasa"). See
// memory/feedback_lab_admin_password.md — never substitute a production value.

(async () => {
  const browser = await chromium.launch({
    headless: false
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('https://dev01.iridium.blue/#login');
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('Administrator');
  await page.getByRole('textbox', { name: 'Password' }).fill('sasa');
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForURL('**/app**');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.locator('a').filter({ hasText: 'Canada' }).click();
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox').first().fill('Pseudo Admin');
  await page.getByRole('textbox').first().press('Tab');
  await page.getByRole('textbox').nth(1).fill('admin@pseudo-co.example');
  await page.getByRole('textbox').nth(1).press('Tab');
  await page.locator('input[type="password"]').fill('sasa');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('checkbox', { name: 'Manufacturing' }).check();
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox').first().fill('Pseudo-Co');
  await page.getByRole('textbox').first().press('Tab');
  await page.getByRole('textbox').nth(1).fill('PSC');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox', { name: 'e.g. "Build tools for' }).fill('Pseudo-wizard demonstration company for acceptance matrix');
  await page.getByRole('textbox', { name: 'e.g. "Build tools for' }).press('Tab');
  await page.getByRole('textbox').nth(1).fill('CAD');
  await page.getByRole('combobox').selectOption('Standard with Numbers');
  await page.getByRole('button', { name: 'Complete Setup' }).click();
  await page.goto('https://dev01.iridium.blue/app');
  await page.close();

  // ---------------------
  await context.close();
  await browser.close();
})();
