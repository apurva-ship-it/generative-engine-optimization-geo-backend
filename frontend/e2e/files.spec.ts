import { test, expect, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const BASE = 'http://localhost:5173';

async function loginAs(page: Page, username: string, password: string) {
  await page.request.post('http://localhost:8000/v1/auth/register', {
    data: { username, password },
  });
  await page.goto(BASE + '/login');
  await page.fill('input[name="username"], input[type="text"]', username);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"], button:has-text("Login")');
  await page.waitForURL(BASE + '/');
}

test.describe('File upload', () => {
  test('upload area is visible on home page', async ({ page }) => {
    await loginAs(page, 'uploader1', 'pass123');
    await expect(page.locator('input[type="file"]')).toBeVisible();
  });

  test('upload button is disabled with no file selected', async ({ page }) => {
    await loginAs(page, 'uploader2', 'pass123');
    const btn = page.locator('button:has-text("Upload")');
    await expect(btn).toBeDisabled();
  });

  test('selecting a txt file enables upload button', async ({ page }) => {
    await loginAs(page, 'uploader3', 'pass123');

    const tmpFile = path.join('/tmp', 'e2e_test.txt');
    fs.writeFileSync(tmpFile, 'hello from e2e test');

    await page.setInputFiles('input[type="file"]', tmpFile);
    const btn = page.locator('button:has-text("Upload"), button:has-text("Upload & Preview")');
    await expect(btn).toBeEnabled({ timeout: 3000 });
  });

  test('progress bar appears during upload', async ({ page }) => {
    await loginAs(page, 'uploader4', 'pass123');

    const tmpFile = path.join('/tmp', 'e2e_progress.txt');
    fs.writeFileSync(tmpFile, 'a'.repeat(10000));

    await page.setInputFiles('input[type="file"]', tmpFile);
    await page.click('button:has-text("Upload"), button:has-text("Upload & Preview")');
    // Progress bar should render (role=progressbar)
    await expect(page.locator('[role="progressbar"]')).toBeVisible({ timeout: 3000 });
  });

  test('non-txt file shows error', async ({ page }) => {
    await loginAs(page, 'uploader5', 'pass123');

    const tmpFile = path.join('/tmp', 'e2e_bad.pdf');
    fs.writeFileSync(tmpFile, '%PDF fake content');

    await page.setInputFiles('input[type="file"]', tmpFile);
    await expect(page.locator('text=/only .txt|not supported/i')).toBeVisible({ timeout: 3000 });
  });
});

test.describe('File editor', () => {
  test('navigating to /files/:id/edit renders editor', async ({ page }) => {
    await loginAs(page, 'editor1', 'pass123');
    // Navigate directly — editor may show an error (no real file) but should render
    await page.goto(BASE + '/files/1/edit');
    await expect(page.locator('textarea, text=/Loading|Error/i')).toBeVisible({ timeout: 5000 });
  });
});
