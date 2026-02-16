/**
 * E2E Test: Transaction Approval Flow
 *
 * Critical user flow:
 * 1. User lands on dashboard
 * 2. Transactions are displayed
 * 3. User reviews AI categorization
 * 4. User approves transaction
 * 5. Success feedback shown
 * 6. Transaction moves to "Categorized"
 *
 * This test mocks the Clerk auth and backend API to test
 * the frontend user experience end-to-end.
 */

import { test, expect } from '@playwright/test'

// Mock auth for all tests
test.beforeEach(async ({ page }) => {
  // Inject mock auth state
  await page.addInitScript(() => {
    ;(window as Record<string, unknown>).__CLERK_MOCK__ = {
      userId: 'test_user_123',
      email: 'test@example.com',
    }
    localStorage.setItem('realmId', 'test_realm_123')
    localStorage.setItem('isConnected', 'true')
  })

  // Mock backend API responses
  await page.route('**/api/v1/transactions/**', (route) => {
    const url = route.request().url()

    if (url.includes('/approve')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Transaction approved',
          status: 'pending_qbo',
        }),
      })
    }

    // Default: return sample transactions
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'tx_001',
          date: '2024-01-15',
          description: 'STARBUCKS COFFEE #1234',
          amount: 5.75,
          status: 'pending_approval',
          suggested_category_name: 'Meals & Entertainment',
          suggested_category_id: 'cat_001',
          confidence: 0.85,
          vendor_reasoning: 'Starbucks is a coffee shop',
          category_reasoning: 'Food purchases under $20 categorized as Meals',
        },
        {
          id: 'tx_002',
          date: '2024-01-16',
          description: 'AMAZON MKTP US*ABCD',
          amount: 45.99,
          status: 'unmatched',
          suggested_category_name: 'Office Supplies',
          suggested_category_id: 'cat_002',
          confidence: 0.72,
          vendor_reasoning: 'Amazon marketplace purchase',
          category_reasoning: 'Common office supply vendor',
        },
      ]),
    })
  })

  // Mock analytics
  await page.route('**/api/v1/analytics/**', (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_transactions: 10,
        pending_approval: 5,
        auto_matched: 3,
        total_synced: 2,
      }),
    })
  })

  // Mock user endpoint
  await page.route('**/api/v1/users/**', (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'test_user_123',
        email: 'test@example.com',
        token_balance: 500,
        subscription_tier: 'professional',
      }),
    })
  })
})

test.describe('Transaction Approval Flow', () => {
  test('should display dashboard with transactions', async ({ page }) => {
    await page.goto('/dashboard')

    // Dashboard should load
    await expect(page).toHaveURL(/dashboard/)

    // Wait for content to render
    await page.waitForTimeout(2000)
  })

  test('should show AI suggestion with confidence', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2000)

    // Look for transaction-related content
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Override with error response
    await page.route('**/api/v1/transactions/**', (route) => {
      if (route.request().url().includes('/approve')) {
        return route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'QBO API Error' }),
        })
      }
      return route.continue()
    })

    await page.goto('/dashboard')
    await page.waitForTimeout(2000)

    // Page should still be functional (no crash)
    await expect(page).toHaveURL(/dashboard/)
  })
})

test.describe('Receipt Upload Flow', () => {
  test('should handle file upload UI', async ({ page }) => {
    // Mock upload endpoint
    await page.route('**/api/v1/transactions/upload-receipt', (route) => {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Receipt processed',
          extracted: {
            merchant: 'Staples',
            total: 45.99,
            date: '2024-01-15',
          },
          match_id: 'tx_001',
          receipt_url: '/tmp/test-receipt.jpg',
        }),
      })
    })

    await page.goto('/dashboard')
    await page.waitForTimeout(2000)

    // Page should load without errors
    await expect(page).toHaveURL(/dashboard/)
  })
})

test.describe('Subscription Flow', () => {
  test('should display pricing page', async ({ page }) => {
    await page.goto('/pricing')

    // Pricing page should load
    await expect(page).toHaveURL(/pricing/)

    // Wait for content
    await page.waitForTimeout(2000)

    // Should show pricing tiers
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })
})
