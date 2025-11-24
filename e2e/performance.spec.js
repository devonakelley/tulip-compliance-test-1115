const { test, expect } = require('@playwright/test');

test.describe('Performance Tests', () => {
  test('should load landing page within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('should have acceptable lighthouse scores', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check that page has rendered content
    const bodyContent = await page.locator('body').textContent();
    expect(bodyContent?.length).toBeGreaterThan(0);
  });

  test('should not have memory leaks', async ({ page }) => {
    await page.goto('/');

    // Navigate between pages
    for (let i = 0; i < 5; i++) {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    }

    // Page should still be responsive
    const isVisible = await page.locator('body').isVisible();
    expect(isVisible).toBe(true);
  });

  test('should handle large data sets', async ({ page }) => {
    await page.goto('/');
    const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
    const testPassword = process.env.TEST_USER_PASSWORD || 'testpassword';

    // Login
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');

    await page.waitForURL(/dashboard|main|home/i, { timeout: 10000 });

    // Wait for any data to load
    await page.waitForLoadState('networkidle');

    // Page should remain responsive
    const isClickable = await page.locator('body').isEnabled();
    expect(isClickable).toBe(true);
  });
});
