import axios from 'axios'

const API_BASE = '/api'
let sessionId = localStorage.getItem('bookstore_session')
if (!sessionId) {
  sessionId = crypto.randomUUID()
  localStorage.setItem('bookstore_session', sessionId)
}

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: inject JWT token and session_id
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('bookstore_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Inject session_id into params for GET/DELETE or body for POST/PUT
  if (['get', 'delete'].includes(config.method)) {
    config.params = { ...config.params, session_id: sessionId }
  } else if (['post', 'put'].includes(config.method) && config.data && typeof config.data === 'object') {
    config.data = { ...config.data, session_id: sessionId }
  }
  return config
})

// Response interceptor: handle 401 globally
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('bookstore_token')
      window.dispatchEvent(new Event('auth-changed'))
      // Optionally redirect to login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export function get(path, params = {}) {
  return client.get(path, { params }).then(r => r.data)
}

export function post(path, body = {}) {
  return client.post(path, body).then(r => r.data)
}

export function put(path, body = {}) {
  return client.put(path, body).then(r => r.data)
}

export function del(path, params = {}) {
  return client.delete(path, { params }).then(r => r.data)
}

export function getToken() {
  return localStorage.getItem('bookstore_token')
}

export function setToken(token) {
  localStorage.setItem('bookstore_token', token)
  window.dispatchEvent(new Event('auth-changed'))
}

export function clearToken() {
  localStorage.removeItem('bookstore_token')
  window.dispatchEvent(new Event('auth-changed'))
}

export function isLoggedIn() {
  return !!getToken()
}

export { client }
