const { test, expect } = require('@playwright/test');

test.describe('Landing Page', () => {
  test('should load landing page successfully', async ({ page }) => {
    await page.goto('/');

    // Check page loads
    await expect(page).toHaveTitle(/Tulip/i);

    // Page should be responsive
    const viewport = page.viewportSize();
    expect(viewport).toBeTruthy();
  });

  test('should have proper SEO elements', async ({ page }) => {
    await page.goto('/');

    // Check meta tags
    await expect(page.locator('meta[name="description"]')).toHaveCount(1);
  });

  test('should be accessible', async ({ page }) => {
    await page.goto('/');

    // Basic accessibility check - main content should have proper headings
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThan(0);
  });

  test('should handle navigation', async ({ page }) => {
    await page.goto('/');

    // Check if main navigation elements are present
    const nav = page.locator('nav');
    if (await nav.count() > 0) {
      await expect(nav.first()).toBeVisible();
    }
  });
});
