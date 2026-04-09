import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

interface User {
  id: string
  email: string
  seller_id: string
  marketplace_id: string
  region: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth-token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      // TODO: Fetch user from API
      setUser({
        id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        email: 'demo@example.com',
        seller_id: 'MOCK-SELLER-001',
        marketplace_id: 'ARBP9OOSHTCHU',
        region: 'EU',
      })
    }
    setLoading(false)
  }, [token])

  const login = async (email: string, password: string) => {
    try {
      const { data } = await api.post('/auth/login', { email, password })
      setToken(data.access_token)
      setUser(data.user)
      localStorage.setItem('auth-token', data.access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
      toast.success('تم تسجيل الدخول بنجاح')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل تسجيل الدخول')
      throw error
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth-token')
    delete api.defaults.headers.common['Authorization']
    toast.success('تم تسجيل الخروج')
  }

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, logout, loading }}>
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
