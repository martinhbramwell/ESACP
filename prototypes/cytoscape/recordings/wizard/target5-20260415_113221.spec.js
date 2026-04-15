const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: false
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('https://target5.iridium.blue/#login');
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('Administrator');
  await page.getByRole('textbox', { name: 'Password' }).fill('sasa');
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForURL('**/app**');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.locator('a').filter({ hasText: 'Canada' }).click();
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox').first().fill('You Yourself');
  await page.getByRole('textbox').first().press('Tab');
  await page.getByRole('textbox').nth(1).fill('yourself.yourorg@gmail.com');
  await page.getByRole('textbox').nth(1).press('Tab');
  await page.locator('input[type="password"]').fill('sasa');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('checkbox', { name: 'Manufacturing' }).check();
  await page.getByRole('checkbox', { name: 'Retail' }).check();
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox').first().fill('Demo Co.');
  await page.getByRole('textbox').first().press('Tab');
  await page.getByRole('textbox').nth(1).fill('DEMO');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox', { name: 'e.g. "Build tools for' }).fill('Demonstrates');
  await page.getByRole('textbox', { name: 'e.g. "Build tools for' }).press('Tab');
  await page.getByRole('textbox').nth(1).fill('TD');
  await page.getByRole('combobox').selectOption('Standard with Numbers');
  await page.getByRole('button', { name: 'Complete Setup' }).click();
  await page.goto('https://target5.iridium.blue/app');
  await page.close();

  // ---------------------
  await context.close();
  await browser.close();
})();
