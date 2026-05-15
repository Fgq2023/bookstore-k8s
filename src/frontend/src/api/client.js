import axios from 'axios'

const API_BASE = '/api'
const sessionId = localStorage.getItem('bookstore_session') || crypto.randomUUID()
localStorage.setItem('bookstore_session', sessionId)

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

export function get(path, params = {}) {
  return client.get(path, { params: { ...params, session_id: sessionId } })
    .then(r => r.data)
}

export function post(path, body = {}) {
  return client.post(path, { ...body, session_id: sessionId })
    .then(r => r.data)
}

export function put(path, body = {}) {
  return client.put(path, { ...body, session_id: sessionId })
    .then(r => r.data)
}

export function del(path, params = {}) {
  return client.delete(path, { params: { ...params, session_id: sessionId } })
    .then(r => r.data)
}
