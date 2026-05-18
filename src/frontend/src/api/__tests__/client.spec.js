import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { isLoggedIn, getToken, setToken, clearToken } from '../../api/client.js'

describe('API Client Helpers', () => {
  let storage = {}

  beforeEach(() => {
    storage = {}
    global.localStorage = {
      getItem: (key) => storage[key] || null,
      setItem: (key, val) => { storage[key] = val },
      removeItem: (key) => { delete storage[key] },
    }
    global.window = { dispatchEvent: vi.fn() }
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('getToken returns null when not set', () => {
    expect(getToken()).toBeNull()
  })

  it('setToken stores token and dispatches event', () => {
    setToken('abc123')
    expect(getToken()).toBe('abc123')
    expect(window.dispatchEvent).toHaveBeenCalledTimes(1)
    const event = window.dispatchEvent.mock.calls[0][0]
    expect(event.type).toBe('auth-changed')
  })

  it('clearToken removes token and dispatches event', () => {
    setToken('abc123')
    clearToken()
    expect(getToken()).toBeNull()
    expect(window.dispatchEvent).toHaveBeenCalledTimes(2)
  })

  it('isLoggedIn returns false when no token', () => {
    expect(isLoggedIn()).toBe(false)
  })

  it('isLoggedIn returns true when token exists', () => {
    setToken('abc123')
    expect(isLoggedIn()).toBe(true)
  })
})
