import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import api from '@/lib/axios'
import toast from 'react-hot-toast'
import type { Seller } from '@/types/api'

interface AuthContextType {
  user: Seller | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Seller | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth-token'))
  const [loading, setLoading] = useState(true)

  // On mount, validate stored token and fetch user
  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setLoading(false)
        return
      }

      try {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        const { data } = await api.get<Seller>('/auth/me')
        setUser(data)
      } catch {
        // Token invalid or expired
        setToken(null)
        setUser(null)
        localStorage.removeItem('auth-token')
        delete api.defaults.headers.common['Authorization']
      } finally {
        setLoading(false)
      }
    }

    validateToken()
  }, [token])

  const login = async (email: string, password: string) => {
    const { data } = await api.post('/auth/login', { email, password })
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('auth-token', data.access_token)
    api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
    toast.success('تم تسجيل الدخول بنجاح')
  }

  const register = async (email: string, password: string, name?: string) => {
    const { data } = await api.post('/auth/register', { email, password, name })
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('auth-token', data.access_token)
    api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
    toast.success('تم إنشاء الحساب بنجاح')
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth-token')
    delete api.defaults.headers.common['Authorization']
    toast.success('تم تسجيل الخروج')
  }

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
