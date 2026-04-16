import axios from 'axios'

// When served by the backend (http://127.0.0.1:8765), use the same origin.
// In Vite dev mode, VITE_API_URL will point to the correct backend port.
const BASE_URL = import.meta.env.VITE_API_URL
  || (typeof window !== 'undefined' && window.location.protocol === 'http:'
      ? `${window.location.protocol}//${window.location.hostname}:${window.location.port}/api/v1`
      : 'http://127.0.0.1:8765/api/v1')

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 180000, // 3 minutes — GitHub uploads can be slow
  headers: { 'Content-Type': 'application/json' },
})

// No auth interceptor — single client desktop app

export default api
