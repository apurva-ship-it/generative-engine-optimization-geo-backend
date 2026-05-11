import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5173';

test.describe('Auth flow', () => {
  test('redirects unauthenticated user to /login', async ({ page }) => {
    await page.goto(BASE + '/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login page renders form', async ({ page }) => {
    await page.goto(BASE + '/login');
    await expect(page.locator('input[name="username"], input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"], button:has-text("Login")')).toBeVisible();
  });

  test('wrong credentials shows error', async ({ page }) => {
    await page.goto(BASE + '/login');
    await page.fill('input[name="username"], input[type="text"]', 'nobody');
    await page.fill('input[type="password"]', 'wrongpass');
    await page.click('button[type="submit"], button:has-text("Login")');
    await expect(page.locator('text=/error|invalid|incorrect/i')).toBeVisible({ timeout: 5000 });
  });

  test('successful login redirects to home', async ({ page, request }) => {
    // Register via API first
    await request.post('http://localhost:8000/v1/auth/register', {
      data: { username: 'e2euser', password: 'testpass123' },
    });

    await page.goto(BASE + '/login');
    await page.fill('input[name="username"], input[type="text"]', 'e2euser');
    await page.fill('input[type="password"]', 'testpass123');
    await page.click('button[type="submit"], button:has-text("Login")');
    await expect(page).toHaveURL(BASE + '/', { timeout: 5000 });
  });

  test('logout button returns to login page', async ({ page, request }) => {
    await request.post('http://localhost:8000/v1/auth/register', {
      data: { username: 'logoutuser', password: 'pass123' },
    });

    await page.goto(BASE + '/login');
    await page.fill('input[name="username"], input[type="text"]', 'logoutuser');
    await page.fill('input[type="password"]', 'pass123');
    await page.click('button[type="submit"], button:has-text("Login")');
    await page.waitForURL(BASE + '/');

    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });
});
