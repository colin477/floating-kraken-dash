import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display login form by default', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('should switch to register form', async ({ page }) => {
    await page.getByText(/sign up/i).click()
    await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible()
    await expect(page.getByLabel(/full name/i)).toBeVisible()
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
  })

  test('should validate required fields on login', async ({ page }) => {
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page.getByText(/email is required/i)).toBeVisible()
    await expect(page.getByText(/password is required/i)).toBeVisible()
  })

  test('should validate email format', async ({ page }) => {
    await page.getByLabel(/email/i).fill('invalid-email')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page.getByText(/invalid email format/i)).toBeVisible()
  })

  test('should handle login error', async ({ page }) => {
    // Mock API response for failed login
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' })
      })
    })

    await page.getByLabel(/email/i).fill('test@example.com')
    await page.getByLabel(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page.getByText(/invalid credentials/i)).toBeVisible()
  })

  test('should successfully login and redirect to dashboard', async ({ page }) => {
    // Mock successful login response
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token',
          refresh_token: 'mock-refresh',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: 'user-id',
            email: 'test@example.com',
            full_name: 'Test User'
          }
        })
      })
    })

    // Mock user profile endpoint
    await page.route('**/api/v1/profile', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'profile-id',
          user_id: 'user-id',
          dietary_restrictions: [],
          allergies: [],
          cooking_skill: 'intermediate'
        })
      })
    })

    await page.getByLabel(/email/i).fill('test@example.com')
    await page.getByLabel(/password/i).fill('password123')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/)
    await expect(page.getByText(/welcome/i)).toBeVisible()
  })

  test('should successfully register new user', async ({ page }) => {
    // Mock successful registration response
    await page.route('**/api/v1/auth/register', async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token',
          refresh_token: 'mock-refresh',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            id: 'new-user-id',
            email: 'newuser@example.com',
            full_name: 'New User'
          }
        })
      })
    })

    await page.getByText(/sign up/i).click()
    await page.getByLabel(/full name/i).fill('New User')
    await page.getByLabel(/email/i).fill('newuser@example.com')
    await page.getByLabel(/password/i).fill('Password123!')
    await page.getByRole('button', { name: /create account/i }).click()

    // Should redirect to profile setup or dashboard
    await expect(page).toHaveURL(/.*profile|.*dashboard/)
  })

  test('should handle registration error for existing email', async ({ page }) => {
    // Mock registration error response
    await page.route('**/api/v1/auth/register', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Email already registered' })
      })
    })

    await page.getByText(/sign up/i).click()
    await page.getByLabel(/full name/i).fill('Test User')
    await page.getByLabel(/email/i).fill('existing@example.com')
    await page.getByLabel(/password/i).fill('Password123!')
    await page.getByRole('button', { name: /create account/i }).click()

    await expect(page.getByText(/email already registered/i)).toBeVisible()
  })
})

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication for dashboard tests
    await page.route('**/api/v1/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'user-id',
          email: 'test@example.com',
          full_name: 'Test User'
        })
      })
    })

    // Set auth token in localStorage
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    await page.goto('/dashboard')
  })

  test('should display main navigation', async ({ page }) => {
    await expect(page.getByRole('navigation')).toBeVisible()
    await expect(page.getByText(/pantry/i)).toBeVisible()
    await expect(page.getByText(/recipes/i)).toBeVisible()
    await expect(page.getByText(/meal plans/i)).toBeVisible()
    await expect(page.getByText(/shopping lists/i)).toBeVisible()
  })

  test('should navigate to pantry page', async ({ page }) => {
    await page.getByText(/pantry/i).click()
    await expect(page).toHaveURL(/.*pantry/)
    await expect(page.getByRole('heading', { name: /pantry/i })).toBeVisible()
  })

  test('should navigate to recipes page', async ({ page }) => {
    await page.getByText(/recipes/i).click()
    await expect(page).toHaveURL(/.*recipes/)
    await expect(page.getByRole('heading', { name: /recipes/i })).toBeVisible()
  })

  test('should logout successfully', async ({ page }) => {
    await page.getByRole('button', { name: /logout/i }).click()
    await expect(page).toHaveURL('/')
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
  })
})

test.describe('Pantry Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    // Mock pantry items API
    await page.route('**/api/v1/pantry/items', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: '1',
              name: 'Tomatoes',
              category: 'vegetables',
              quantity: 5,
              unit: 'pieces',
              expiry_date: '2024-12-31',
              location: 'refrigerator'
            }
          ])
        })
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '2',
            name: 'New Item',
            category: 'vegetables',
            quantity: 1,
            unit: 'piece',
            location: 'pantry'
          })
        })
      }
    })

    await page.goto('/pantry')
  })

  test('should display pantry items', async ({ page }) => {
    await expect(page.getByText('Tomatoes')).toBeVisible()
    await expect(page.getByText('5 pieces')).toBeVisible()
    await expect(page.getByText('refrigerator')).toBeVisible()
  })

  test('should add new pantry item', async ({ page }) => {
    await page.getByRole('button', { name: /add item/i }).click()
    
    await page.getByLabel(/name/i).fill('New Item')
    await page.getByLabel(/category/i).selectOption('vegetables')
    await page.getByLabel(/quantity/i).fill('1')
    await page.getByLabel(/unit/i).fill('piece')
    await page.getByLabel(/location/i).selectOption('pantry')
    
    await page.getByRole('button', { name: /save/i }).click()
    
    await expect(page.getByText('New Item')).toBeVisible()
  })

  test('should filter pantry items by category', async ({ page }) => {
    await page.getByLabel(/filter by category/i).selectOption('vegetables')
    await expect(page.getByText('Tomatoes')).toBeVisible()
    
    await page.getByLabel(/filter by category/i).selectOption('fruits')
    await expect(page.getByText('Tomatoes')).not.toBeVisible()
  })
})

test.describe('Responsive Design', () => {
  test('should work on mobile devices', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')
    
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
  })

  test('should have accessible navigation on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })
    
    await page.goto('/dashboard')
    
    // Should have mobile menu button
    await expect(page.getByRole('button', { name: /menu/i })).toBeVisible()
    
    // Open mobile menu
    await page.getByRole('button', { name: /menu/i }).click()
    await expect(page.getByText(/pantry/i)).toBeVisible()
  })
})