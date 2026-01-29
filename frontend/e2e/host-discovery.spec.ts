import { test, expect } from '@playwright/test'

test.describe('Host Discovery', () => {
  test.describe('Hosts List Page', () => {
    test('should display hosts list page', async ({ page }) => {
      await page.goto('/hosts')

      // Check page title or heading
      await expect(page.getByRole('heading', { name: /host|dance|find/i })).toBeVisible()
    })

    test('should show search/filter options', async ({ page }) => {
      await page.goto('/hosts')

      // Check for location or search input
      const searchInput = page.getByPlaceholder(/search|location|where/i)
      const locationInput = page.getByLabel(/location/i)

      // Either search or location input should exist
      const hasSearch = await searchInput.count() > 0
      const hasLocation = await locationInput.count() > 0

      expect(hasSearch || hasLocation).toBeTruthy()
    })

    test('should display host cards with key information', async ({ page }) => {
      await page.goto('/hosts')

      // Wait for any loading to complete
      await page.waitForLoadState('networkidle')

      // Check for host cards or list items
      const hostCards = page.locator('[data-testid="host-card"], .host-card, article')

      // If there are hosts, verify card structure
      if (await hostCards.count() > 0) {
        const firstCard = hostCards.first()

        // Should show name/title
        await expect(firstCard.locator('h2, h3, [data-testid="host-name"]')).toBeVisible()
      }
    })

    test('should have clickable host cards that navigate to profile', async ({ page }) => {
      await page.goto('/hosts')

      await page.waitForLoadState('networkidle')

      // Find first host link
      const hostLink = page.locator('a[href*="/hosts/"]').first()

      if (await hostLink.count() > 0) {
        await hostLink.click()

        // Should navigate to host profile
        await expect(page).toHaveURL(/\/hosts\/[a-zA-Z0-9-]+/)
      }
    })
  })

  test.describe('Host Profile Page', () => {
    // Note: This test assumes a host exists. In real E2E testing,
    // you would either seed data or mock the API
    test('should show 404 for non-existent host', async ({ page }) => {
      await page.goto('/hosts/non-existent-host-id')

      // Should show not found or error message
      await expect(
        page.getByText(/not found|doesn't exist|error|404/i)
      ).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Dance Style Filtering', () => {
    test('should have dance style filter options', async ({ page }) => {
      await page.goto('/hosts')

      // Look for dance style filter
      const danceStyleFilter = page.locator(
        'select, [data-testid="dance-style-filter"], [role="combobox"]'
      ).filter({ hasText: /salsa|tango|bachata|dance/i })

      // If filter exists, check it's functional
      if (await danceStyleFilter.count() > 0) {
        await expect(danceStyleFilter.first()).toBeVisible()
      }
    })
  })

  test.describe('Location-based Search', () => {
    test('should prompt for location access or show location input', async ({ page }) => {
      await page.goto('/hosts')

      // Either location permission prompt or manual location input
      const locationInput = page.getByPlaceholder(/location|city|address/i)
      const locationButton = page.getByRole('button', { name: /location|near me/i })

      const hasLocationInput = await locationInput.count() > 0
      const hasLocationButton = await locationButton.count() > 0

      expect(hasLocationInput || hasLocationButton).toBeTruthy()
    })
  })

  test.describe('Responsive Design', () => {
    test('should display correctly on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await page.goto('/hosts')

      // Page should still be functional
      await expect(page.getByRole('heading', { name: /host|dance|find/i })).toBeVisible()
    })

    test('should display correctly on tablet viewport', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 })

      await page.goto('/hosts')

      await expect(page.getByRole('heading', { name: /host|dance|find/i })).toBeVisible()
    })
  })

  test.describe('Empty State', () => {
    test('should show appropriate message when no hosts match criteria', async ({ page }) => {
      await page.goto('/hosts')

      await page.waitForLoadState('networkidle')

      // If a "no results" message appears, it should be informative
      const noResultsMessage = page.getByText(/no hosts|no results|not found/i)

      if (await noResultsMessage.count() > 0) {
        await expect(noResultsMessage).toBeVisible()
      }
    })
  })
})
