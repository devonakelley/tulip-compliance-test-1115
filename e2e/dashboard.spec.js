const { test, expect } = require('@playwright/test');

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
    const testPassword = process.env.TEST_USER_PASSWORD || 'testpassword';

    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');

    await page.waitForURL(/dashboard|main|home/i, { timeout: 10000 });
  });

  test('should display dashboard components', async ({ page }) => {
    // Dashboard should have main content
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to regulatory dashboard', async ({ page }) => {
    // Look for regulatory dashboard link or navigation
    const regulatoryLink = page.locator('text=/regulatory/i').first();
    if (await regulatoryLink.count() > 0) {
      await regulatoryLink.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/regulatory/i);
    }
  });

  test('should load without errors', async ({ page }) => {
    const errors = [];
    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    await page.waitForLoadState('networkidle');

    // Should have no critical errors
    expect(errors.filter(e => !e.includes('Warning'))).toHaveLength(0);
  });

  test('should handle responsive design', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForLoadState('networkidle');

    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent).toBeVisible();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForLoadState('networkidle');
    await expect(mainContent).toBeVisible();
  });
});
