import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8766/api/v1',
  timeout: 180000, // 3 minutes — GitHub uploads can be slow
  headers: { 'Content-Type': 'application/json' },
})

// No auth interceptor — single client desktop app

export default api
