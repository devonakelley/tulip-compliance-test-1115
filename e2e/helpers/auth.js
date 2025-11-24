/**
 * Authentication helpers for E2E tests
 */

/**
 * Login helper function
 * @param {import('@playwright/test').Page} page - Playwright page object
 * @param {string} email - User email
 * @param {string} password - User password
 */
async function login(page, email, password) {
  await page.goto('/');
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/dashboard|main|home/i, { timeout: 10000 });
}

/**
 * Logout helper function
 * @param {import('@playwright/test').Page} page - Playwright page object
 */
async function logout(page) {
  const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out")');
  await logoutButton.click();
  await page.waitForURL(/login|^\/$/, { timeout: 5000 });
}

/**
 * Get test credentials from environment
 * @returns {{email: string, password: string}}
 */
function getTestCredentials() {
  return {
    email: process.env.TEST_USER_EMAIL || 'test@example.com',
    password: process.env.TEST_USER_PASSWORD || 'testpassword',
  };
}

module.exports = {
  login,
  logout,
  getTestCredentials,
};
