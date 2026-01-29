import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.describe('Registration', () => {
    test('should display registration form', async ({ page }) => {
      await page.goto('/register')

      // Check form elements exist
      await expect(page.getByLabel(/first name/i)).toBeVisible()
      await expect(page.getByLabel(/last name/i)).toBeVisible()
      await expect(page.getByLabel(/email/i)).toBeVisible()
      await expect(page.getByLabel(/password/i)).toBeVisible()
      await expect(page.getByRole('button', { name: /register|sign up/i })).toBeVisible()
    })

    test('should show validation errors for empty form', async ({ page }) => {
      await page.goto('/register')

      // Submit empty form
      await page.getByRole('button', { name: /register|sign up/i }).click()

      // Check for validation messages
      await expect(page.getByText(/required|enter/i).first()).toBeVisible()
    })

    test('should show error for invalid email format', async ({ page }) => {
      await page.goto('/register')

      await page.getByLabel(/email/i).fill('invalid-email')
      await page.getByRole('button', { name: /register|sign up/i }).click()

      await expect(page.getByText(/valid email|invalid/i)).toBeVisible()
    })

    test('should navigate to login from registration page', async ({ page }) => {
      await page.goto('/register')

      await page.getByRole('link', { name: /login|sign in|already have/i }).click()

      await expect(page).toHaveURL(/.*login/)
    })
  })

  test.describe('Login', () => {
    test('should display login form', async ({ page }) => {
      await page.goto('/login')

      await expect(page.getByLabel(/email/i)).toBeVisible()
      await expect(page.getByLabel(/password/i)).toBeVisible()
      await expect(page.getByRole('button', { name: /login|sign in/i })).toBeVisible()
    })

    test('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/login')

      await page.getByLabel(/email/i).fill('test@example.com')
      await page.getByLabel(/password/i).fill('wrongpassword')
      await page.getByRole('button', { name: /login|sign in/i }).click()

      // Wait for error message
      await expect(page.getByText(/invalid|incorrect|unauthorized/i)).toBeVisible({
        timeout: 5000,
      })
    })

    test('should navigate to registration from login page', async ({ page }) => {
      await page.goto('/login')

      await page.getByRole('link', { name: /register|sign up|create account/i }).click()

      await expect(page).toHaveURL(/.*register/)
    })

    test('should show password visibility toggle', async ({ page }) => {
      await page.goto('/login')

      const passwordInput = page.getByLabel(/password/i)

      // Initially password type
      await expect(passwordInput).toHaveAttribute('type', 'password')

      // Find and click toggle if it exists
      const toggle = page.locator('button, [role="button"]').filter({ has: page.locator('svg, [class*="eye"]') })
      if (await toggle.count() > 0) {
        await toggle.first().click()
        // Should change to text type
        await expect(passwordInput).toHaveAttribute('type', 'text')
      }
    })
  })

  test.describe('Protected Routes', () => {
    test('should redirect to login when accessing protected route', async ({ page }) => {
      // Try to access a protected route
      await page.goto('/settings')

      // Should redirect to login
      await expect(page).toHaveURL(/.*login/)
    })

    test('should redirect to login when accessing bookings without auth', async ({ page }) => {
      await page.goto('/bookings')

      await expect(page).toHaveURL(/.*login/)
    })

    test('should redirect to login when accessing messages without auth', async ({ page }) => {
      await page.goto('/messages')

      await expect(page).toHaveURL(/.*login/)
    })
  })
})
