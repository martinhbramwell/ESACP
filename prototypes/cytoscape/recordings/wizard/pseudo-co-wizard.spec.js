const { chromium } = require('playwright');

// ─────────────────────────────────────────────────────────────────────────────
// ERPNext setup-wizard replay — parameterised (#181).
//
// Default config below reproduces the Pseudo-Co run used by acceptance matrix
// Run 03 (CLI) and Run 06 (UI). B03 and B06 are captured by the downstream
// pipeline; parity between the two is the matrix contract.
//
// Override the entire config by setting WIZARD_CONFIG_JSON to a JSON literal
// matching DEFAULT_CONFIG's shape. replay_wizard.js forwards that env var into
// the child Node process when invoked with --config <json-file>.
//
// replay_wizard.js also rewrites the hardcoded dev01 URL below to the caller's
// --url target at replay time, so the goto() URL here is a template only.
//
// Password 'sasa' is the dev-lab value sourced from config/build_secrets.sops.yml
// (erp_user_pwd). See memory/feedback_lab_admin_password.md — never substitute a
// production value.
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_CONFIG = {
  admin: {
    login_user:     'Administrator',
    login_password: 'sasa',
    full_name:      'Pseudo Admin',
    email:          'admin@pseudo-co.example',
    password:       'sasa',
  },
  country: 'Canada',
  industries: ['Manufacturing'],
  company: {
    name:                 'Pseudo-Co',
    abbr:                 'PSC',
    description:          'Pseudo-wizard demonstration company for acceptance matrix',
    currency:             'CAD',
    accounting_standard:  'Standard with Numbers',
  },
};

const CONFIG = process.env.WIZARD_CONFIG_JSON
  ? JSON.parse(process.env.WIZARD_CONFIG_JSON)
  : DEFAULT_CONFIG;

// ── Helper: wait for Frappe's AJAX freeze backdrop to clear ──────────────
// Fixes #293. Every wizard-navigation click (Next / Complete Setup) must be
// preceded by this guard. Frappe's setup_wizard POSTs per screen and the
// freeze backdrop (#freeze.modal-backdrop.in) intercepts pointer events
// until the response lands. Under pipeline load (Python subprocess + the
// idempotency-verify SSH probes that run just before wizard_run.py), the
// clearance time crosses the click tolerance on un-guarded Next clicks.
// A recording-side per-click wait adapts to load; pipeline-side fixed
// warmup would only guard the first click.
async function waitForFrappeIdle(page, timeout = 30_000) {
  await page.waitForFunction(
    () => !document.querySelector('#freeze.modal-backdrop.in'),
    null, { timeout },
  );
}

// ── Helper: dismiss Frappe's welcome/onboarding modal ───────────────────
// Fixes #297 (which extends #284/#293). The onboarding modal
// (.modal-backdrop.show / .modal.show) materialises asynchronously at
// non-deterministic wizard transitions, intercepting pointer events.
// waitForFrappeIdle does NOT cover this — it checks #freeze.modal-backdrop.in,
// a different selector for Frappe's AJAX freeze indicator.
//
// Escape dismisses it in most cases (2 s budget). Under pipeline load the
// Escape key is intermittently consumed by something other than the modal
// (focus trap races, ancestor handlers); the DOM-remove fallback then
// strips the backdrop directly so the next click always lands.
//
// Idempotent: returns immediately if no modal is visible. Safe to call
// before every wizard interaction.
async function dismissWelcomeModal(page, timeout = 2_000) {
  const visible = await page.locator('.modal-backdrop.show').first()
    .isVisible().catch(() => false);
  if (!visible) return;
  await page.keyboard.press('Escape');
  const dismissed = await page.waitForFunction(
    () => !document.querySelector('.modal-backdrop.show'),
    null, { timeout },
  ).then(() => true).catch(() => false);
  if (dismissed) return;
  await page.evaluate(() => {
    document.querySelectorAll('.modal-backdrop, .modal.show, .modal.fade.show').forEach(n => n.remove());
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('overflow');
    document.body.style.removeProperty('padding-right');
  });
  await page.waitForFunction(
    () => !document.querySelector('.modal-backdrop.show') && !document.querySelector('.modal.show'),
    null, { timeout },
  );
}

// ── Composite guard for transitions where the welcome modal has been observed ─
// Use at known-bad transitions only (#284 Industry-Next, #297 Company-name-Next,
// #296 Complete-Setup). Calling at every wizard step regressed: the DOM-remove
// fallback or stray Escape can interfere with screen-render timing at
// transitions where no welcome modal is actually present.
async function readyForInteraction(page) {
  await waitForFrappeIdle(page);
  await dismissWelcomeModal(page);
}

(async () => {
  const browser = await chromium.launch({
    headless: false
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  // ── Login ────────────────────────────────────────────────────────────────
  // Fixes #293. Playwright's default waitForURL timeout is 30 s; when the
  // wizard runs right after the pipeline's Stage 8 supervisor restart, the
  // client can sit idle for ~29 s between login POST and the /app redirect
  // (workers/redis warming up), hitting the default. 90 s absorbs that.
  await page.goto('https://dev01.iridium.blue/#login');
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill(CONFIG.admin.login_user);
  await page.getByRole('textbox', { name: 'Password' }).fill(CONFIG.admin.login_password);
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForURL('**/app**', { timeout: 90_000 });

  // ── Wizard screen 1: Welcome + Country ───────────────────────────────────
  await waitForFrappeIdle(page);
  await page.getByRole('button', { name: 'Next' }).click();
  await page.locator('a').filter({ hasText: CONFIG.country }).click();
  await waitForFrappeIdle(page);
  await page.getByRole('button', { name: 'Next' }).click();

  // ── Wizard screen 2: User ────────────────────────────────────────────────
  await page.getByRole('textbox').first().fill(CONFIG.admin.full_name);
  await page.getByRole('textbox').first().press('Tab');
  await page.getByRole('textbox').nth(1).fill(CONFIG.admin.email);
  await page.getByRole('textbox').nth(1).press('Tab');
  await page.locator('input[type="password"]').fill(CONFIG.admin.password);
  await waitForFrappeIdle(page);
  await page.getByRole('button', { name: 'Next' }).click();

  // ── Wizard screen 3: Industry ────────────────────────────────────────────
  // Wait for Frappe's AJAX freeze overlay to clear before Industry-page
  // interaction (#256 flake guard — does not cover the welcome-modal race,
  // which is handled below).
  await waitForFrappeIdle(page);
  // Fixes #267. Run 06 attempt 1 showed the welcome modal can materialise
  // DURING Playwright's .check() retry loop, not just before it — a
  // pre-click Escape guard cannot see the future. Resolve each checkbox
  // via the role locator, then mutate it directly in the page origin:
  // the assignment + event dispatch runs synchronously and does not
  // compete with any overlay. Verify via isChecked() so that if Frappe
  // did not observe the change (e.g. custom component swallowing native
  // events), we fail immediately instead of passing a broken wizard.
  for (const industry of CONFIG.industries) {
    const cb = page.getByRole('checkbox', { name: industry });
    await cb.waitFor({ state: 'attached', timeout: 30_000 });
    await cb.evaluate((el) => {
      if (!el.checked) {
        el.checked = true;
        el.dispatchEvent(new Event('input',  { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    if (!(await cb.isChecked())) {
      throw new Error(`${industry} checkbox did not register as checked after DOM mutation`);
    }
  }
  // #267 + #284 + #293: welcome modal can materialise AFTER the checkbox
  // DOM mutation and before this Next click. dismissWelcomeModal (called via
  // readyForInteraction) handles Escape + DOM-remove fallback.
  await readyForInteraction(page);
  await page.getByRole('button', { name: 'Next' }).click();

  // ── Wizard screen 4a: Company name + abbr ────────────────────────────────
  await waitForFrappeIdle(page);
  await page.getByRole('textbox').first().fill(CONFIG.company.name);
  await page.getByRole('textbox').first().press('Tab');
  await page.getByRole('textbox').nth(1).fill(CONFIG.company.abbr);
  await readyForInteraction(page);
  await page.getByRole('button', { name: 'Next' }).click();

  // ── Wizard screen 4b: Company description, currency, accounting standard ─
  await page.getByRole('textbox', { name: 'e.g. "Build tools for' }).fill(CONFIG.company.description);
  await page.getByRole('textbox', { name: 'e.g. "Build tools for' }).press('Tab');
  await page.getByRole('textbox').nth(1).fill(CONFIG.company.currency);
  await page.getByRole('combobox').selectOption(CONFIG.company.accounting_standard);

  // ── Complete Setup ───────────────────────────────────────────────────────
  // Fixes #256. The setup_wizard.setup_complete handler is synchronous
  // through Company INSERT + Chart-of-Accounts seeding (~30–45s). Wait for
  // the POST response itself — page.waitForFunction(async fn) returned
  // truthy prematurely in earlier attempts, producing pre-seed backups.
  await readyForInteraction(page);
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

  // ── Canary: verify Company exists and CoA seeding completed ──────────────
  // Belt-and-braces — page.evaluate runs fetch in the page's own origin,
  // dodging both the waitForFunction async-truthy quirk (attempt 4) and
  // page.request's absolute-URL requirement (attempt 6). default_bank_account
  // is only populated once CoA seeding finishes, so its presence proves the
  // full handler chain ran end-to-end.
  const companyName = CONFIG.company.name;
  const check = await page.evaluate(async (name) => {
    try {
      const r = await fetch(`/api/resource/Company/${encodeURIComponent(name)}`, { credentials: 'include' });
      if (!r.ok) return { ok: false, status: r.status };
      const ct = r.headers.get('content-type') || '';
      if (!ct.includes('application/json')) return { ok: false, reason: 'non-json' };
      const j = await r.json();
      return { ok: true, data: j?.data };
    } catch (err) { return { ok: false, reason: String(err) }; }
  }, companyName);
  if (!check.ok) {
    throw new Error(`Company/${companyName} check failed: ${JSON.stringify(check)}`);
  }
  if (!check.data?.default_bank_account) {
    throw new Error(`Company/${companyName} default_bank_account empty — CoA seeding incomplete`);
  }
  await page.close();

  // ---------------------
  await context.close();
  await browser.close();
})();
