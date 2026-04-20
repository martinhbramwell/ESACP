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
  // Flake guard: the Industry page occasionally shows a Bootstrap welcome
  // modal that intercepts pointer events on the checkbox (attempts 3 and 5
  // of #256 blocked > 30s here). Wait for Frappe's AJAX freeze to clear,
  // then Escape-dismiss any lingering modal before the checkbox click.
  await page.waitForFunction(
    () => !document.querySelector('#freeze.modal-backdrop.in'),
    null, { timeout: 30_000 },
  );
  if (await page.locator('.modal.fade.show').count()) {
    await page.keyboard.press('Escape');
    await page.waitForSelector('.modal.fade.show', { state: 'detached', timeout: 10_000 });
  }
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
  // Fixes #256. The setup_wizard.setup_complete handler is synchronous
  // through Company INSERT + Chart-of-Accounts seeding (~30–45s). Wait for
  // the POST response itself — page.waitForFunction(async fn) returned
  // truthy prematurely in earlier attempts, producing pre-seed backups.
  const [completeResp] = await Promise.all([
    page.waitForResponse(
      r => /setup_complete/.test(r.url()) && r.request().method() === 'POST',
      { timeout: 180_000 },
    ),
    page.getByRole('button', { name: 'Complete Setup' }).click(),
  ]);
  if (!completeResp.ok()) {
    throw new Error(`setup_complete returned HTTP ${completeResp.status()}`);
  }
  // Belt-and-braces — page.evaluate runs fetch in the page's own origin,
  // dodging both the waitForFunction async-truthy quirk (attempt 4) and
  // page.request's absolute-URL requirement (attempt 6). default_bank_account
  // is only populated once CoA seeding finishes, so its presence proves the
  // full handler chain ran end-to-end.
  const check = await page.evaluate(async () => {
    try {
      const r = await fetch('/api/resource/Company/Pseudo-Co', { credentials: 'include' });
      if (!r.ok) return { ok: false, status: r.status };
      const ct = r.headers.get('content-type') || '';
      if (!ct.includes('application/json')) return { ok: false, reason: 'non-json' };
      const j = await r.json();
      return { ok: true, data: j?.data };
    } catch (err) { return { ok: false, reason: String(err) }; }
  });
  if (!check.ok) {
    throw new Error(`Company/Pseudo-Co check failed: ${JSON.stringify(check)}`);
  }
  if (!check.data?.default_bank_account) {
    throw new Error('Company/Pseudo-Co default_bank_account empty — CoA seeding incomplete');
  }
  await page.close();

  // ---------------------
  await context.close();
  await browser.close();
})();
