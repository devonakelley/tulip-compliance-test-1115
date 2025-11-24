const { test, expect } = require('@playwright/test');

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page', async ({ page }) => {
    await expect(page).toHaveTitle(/Tulip/i);
    // Check if login form is present
    const loginForm = page.locator('form');
    await expect(loginForm).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in login form with invalid credentials
    await page.fill('input[type="email"]', 'invalid@example.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Wait for error message
    await expect(page.locator('text=/invalid|error|incorrect/i')).toBeVisible({ timeout: 5000 });
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Note: Update with actual test credentials or use environment variables
    const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
    const testPassword = process.env.TEST_USER_PASSWORD || 'testpassword';

    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard or main app
    await expect(page).toHaveURL(/dashboard|main|home/i, { timeout: 10000 });
  });

  test('should persist login session', async ({ page, context }) => {
    const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
    const testPassword = process.env.TEST_USER_PASSWORD || 'testpassword';

    // Login
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');

    // Wait for successful login
    await page.waitForURL(/dashboard|main|home/i, { timeout: 10000 });

    // Create new page in same context
    const newPage = await context.newPage();
    await newPage.goto('/');

    // Should still be logged in
    await expect(newPage).toHaveURL(/dashboard|main|home/i, { timeout: 5000 });
  });

  test('should logout successfully', async ({ page }) => {
    const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
    const testPassword = process.env.TEST_USER_PASSWORD || 'testpassword';

    // Login first
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard|main|home/i, { timeout: 10000 });

    // Find and click logout button
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out")');
    await logoutButton.click();

    // Should redirect to login page
    await expect(page).toHaveURL(/login|^\/$/, { timeout: 5000 });
  });
});
