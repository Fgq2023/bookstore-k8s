import { test, expect } from '@playwright/test'

/**
 * End-to-end browser tests for the Bookstore SPA.
 *
 * These tests intercept API calls via page.route() to provide deterministic
 * responses, ensuring the frontend UI behaviour is tested independently of
 * backend state.
 */

const mockBooks = [
  { id: 1, title: 'Clean Code', author: 'Robert C. Martin', isbn: '978-0132350884', price: 42.99, stock_quantity: 10 },
  { id: 2, title: 'Design Patterns', author: 'Gang of Four', isbn: '978-0201633610', price: 54.00, stock_quantity: 5 },
]

const mockUser = {
  username: 'e2e_user',
  email: 'e2e@test.com',
  token: 'mock-jwt-token-for-e2e',
}

const mockCart = {
  items: [
    { id: 101, book_id: 1, title: 'Clean Code', author: 'Robert C. Martin', price: 42.99, quantity: 2 },
  ],
  total: 85.98,
}

const mockOrder = {
  order_id: 501,
  status: 'confirmed',
  items: mockCart.items,
}

const mockPaidOrder = {
  ...mockOrder,
  status: 'shipped',
}

test.beforeEach(async ({ page }) => {
  // Clear localStorage to start fresh
  await page.addInitScript(() => {
    localStorage.clear()
  })

  // Intercept API calls and return mock data
  await page.route('**/api/books**', async (route) => {
    const url = route.request().url()
    if (url.includes('/search')) {
      const q = new URL(url).searchParams.get('q') || ''
      const filtered = mockBooks.filter(b =>
        b.title.toLowerCase().includes(q.toLowerCase()) ||
        b.author.toLowerCase().includes(q.toLowerCase())
      )
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ query: q, count: filtered.length, books: filtered }),
      })
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ count: mockBooks.length, total: mockBooks.length, page: 1, per_page: 20, books: mockBooks }),
      })
    }
  })

  await page.route('**/api/auth/login**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { token: mockUser.token, user: { username: mockUser.username, email: mockUser.email } } }),
    })
  })

  await page.route('**/api/auth/me**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { username: mockUser.username, email: mockUser.email } }),
    })
  })

  await page.route('**/api/cart**', async (route) => {
    const method = route.request().method()
    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockCart),
      })
    } else if (method === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'added', message: 'Item added to cart' }),
      })
    } else if (method === 'PUT') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'updated' }),
      })
    } else if (method === 'DELETE') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'removed' }),
      })
    }
  })

  await page.route('**/api/orders**', async (route) => {
    const method = route.request().method()
    const url = route.request().url()
    if (method === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'created', order_id: mockOrder.order_id }),
      })
    } else if (url.includes('/501')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPaidOrder),
      })
    } else {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ total: 1, orders: [mockPaidOrder] }),
      })
    }
  })

  await page.route('**/api/payments**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: { payment_status: 'paid', order_status: 'shipped', order_id: 501 } }),
    })
  })
})

test('guest can browse and search books', async ({ page }) => {
  await page.goto('/')

  // Should display book list
  await expect(page.getByText('Clean Code')).toBeVisible()
  await expect(page.getByText('Design Patterns')).toBeVisible()

  // Search functionality
  await page.getByPlaceholder('Search by title or author...').fill('Clean')
  await page.getByRole('button', { name: 'Search' }).click()

  await expect(page.getByText('Clean Code')).toBeVisible()
  await expect(page.getByText('Design Patterns')).not.toBeVisible()

  // Reset
  await page.getByRole('button', { name: 'Reset' }).click()
  await expect(page.getByText('Design Patterns')).toBeVisible()
})

test('user can log in and view profile', async ({ page }) => {
  await page.goto('/login')

  await page.getByPlaceholder('johndoe').fill(mockUser.username)
  await page.getByPlaceholder('••••••').fill('Password123!')
  await page.getByRole('button', { name: 'Sign In' }).click()

  // Should redirect to home after login
  await expect(page).toHaveURL('/')

  // Navigate to profile
  await page.getByRole('link', { name: 'Profile' }).click()
  await expect(page).toHaveURL('/profile')
  await expect(page.getByText(mockUser.username)).toBeVisible()
})

test('full shopping flow: browse -> add to cart -> place order -> pay', async ({ page }) => {
  // 1. Start as logged-in user
  await page.goto('/login')
  await page.getByPlaceholder('johndoe').fill(mockUser.username)
  await page.getByPlaceholder('••••••').fill('Password123!')
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page).toHaveURL('/')

  // 2. Add book to cart from book list
  const addButtons = page.getByRole('button', { name: 'Add to Cart' })
  await expect(addButtons.first()).toBeVisible()
  await addButtons.first().click()

  // 3. Go to cart
  await page.getByRole('link', { name: 'Cart' }).click()
  await expect(page).toHaveURL('/cart')
  await expect(page.getByText('Clean Code')).toBeVisible()
  await expect(page.getByText('Total: $85.98')).toBeVisible()

  // 4. Place order
  await page.getByRole('button', { name: 'Place Order' }).click()

  // 5. Should redirect to orders page
  await expect(page).toHaveURL('/orders')
  await expect(page.getByText('shipped')).toBeVisible()
})
