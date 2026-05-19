import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const server = setupServer()

// These will be populated by dynamic import in beforeAll
let get, post, put, del, setToken, clearToken, client

beforeAll(async () => {
  server.listen({ onUnhandledRequest: 'error' })

  // Setup browser globals before importing client module
  const mockSessionId = 'test-session-123'
  const storage = { bookstore_session: mockSessionId }
  global.localStorage = {
    getItem: vi.fn((key) => storage[key] ?? null),
    setItem: vi.fn((key, val) => { storage[key] = val }),
    removeItem: vi.fn((key) => { delete storage[key] }),
  }
  global.window = {
    dispatchEvent: vi.fn(),
    location: { href: 'http://localhost:3000', pathname: '/' }
  }
  global.location = new URL('http://localhost:3000')

  if (!global.crypto) {
    Object.defineProperty(global, 'crypto', {
      value: { randomUUID: vi.fn(() => 'mock-uuid-123') },
      writable: true,
      configurable: true
    })
  } else {
    vi.spyOn(global.crypto, 'randomUUID').mockReturnValue('mock-uuid-123')
  }

  // Dynamic import after environment is fully mocked
  const mod = await import('../client.js')
  get = mod.get
  post = mod.post
  put = mod.put
  del = mod.del
  setToken = mod.setToken
  clearToken = mod.clearToken
  client = mod.client
  client.defaults.baseURL = 'http://localhost:3000/api'
})

afterEach(() => {
  server.resetHandlers()
  vi.clearAllMocks()
  clearToken()
  window.location.href = 'http://localhost:3000'
  window.location.pathname = '/'
})

afterAll(() => {
  server.close()
})

describe('API Client Integration with MSW', () => {
  it('get() appends session_id to query params', async () => {
    let capturedUrl
    server.use(
      http.get('http://localhost:3000/api/books', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({
          count: 1,
          total: 1,
          page: 1,
          per_page: 20,
          books: [{ id: '1', title: 'Test Book', author: 'Tester', price: 9.99 }]
        })
      })
    )

    const data = await get('/books')
    expect(data.books).toHaveLength(1)
    expect(data.books[0].title).toBe('Test Book')

    const url = new URL(capturedUrl)
    expect(url.searchParams.get('session_id')).toBe('test-session-123')
  })

  it('post() injects session_id into request body', async () => {
    let requestBody
    server.use(
      http.post('http://localhost:3000/api/cart', async ({ request }) => {
        requestBody = await request.json()
        return HttpResponse.json({ status: 'added', book_id: '5', quantity: 2 }, { status: 201 })
      })
    )

    const data = await post('/cart', { book_id: '5', quantity: 2 })
    expect(data.status).toBe('added')
    expect(requestBody.session_id).toBe('test-session-123')
    expect(requestBody.book_id).toBe('5')
    expect(requestBody.quantity).toBe(2)
  })

  it('request interceptor injects JWT token into Authorization header', async () => {
    setToken('my-jwt-token')

    let authHeader
    server.use(
      http.get('http://localhost:3000/api/orders', ({ request }) => {
        authHeader = request.headers.get('authorization')
        return HttpResponse.json({ count: 0, total: 0, page: 1, per_page: 20, orders: [] })
      })
    )

    await get('/orders')
    expect(authHeader).toBe('Bearer my-jwt-token')
  })

  it('response interceptor handles 401 by clearing token and redirecting to login', async () => {
    server.use(
      http.get('http://localhost:3000/api/admin/metrics', () => {
        return HttpResponse.json({ error: 'Unauthorized' }, { status: 401 })
      })
    )

    setToken('expired-token')
    window.location.pathname = '/dashboard'

    await expect(get('/admin/metrics')).rejects.toThrow()

    expect(localStorage.removeItem).toHaveBeenCalledWith('bookstore_token')
    expect(window.dispatchEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'auth-changed' })
    )
    expect(window.location.href).toBe('/login')
  })

  it('put() sends session_id in body and returns updated data', async () => {
    let requestBody
    server.use(
      http.put('http://localhost:3000/api/cart/item/1', async ({ request }) => {
        requestBody = await request.json()
        return HttpResponse.json({ status: 'updated', item_id: 1, quantity: 3 })
      })
    )

    const data = await put('/cart/item/1', { quantity: 3 })
    expect(data.status).toBe('updated')
    expect(data.quantity).toBe(3)
    expect(requestBody.session_id).toBe('test-session-123')
  })

  it('del() sends session_id in query string', async () => {
    let capturedUrl
    server.use(
      http.delete('http://localhost:3000/api/cart/item/1', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({ status: 'deleted', item_id: 1 })
      })
    )

    const data = await del('/cart/item/1')
    expect(data.status).toBe('deleted')

    const url = new URL(capturedUrl)
    expect(url.searchParams.get('session_id')).toBe('test-session-123')
  })

  it('get() propagates server errors as rejected promises', async () => {
    server.use(
      http.get('http://localhost:3000/api/books/999', () => {
        return HttpResponse.json({ error: 'not found' }, { status: 404 })
      })
    )

    await expect(get('/books/999')).rejects.toThrow()
  })
})
