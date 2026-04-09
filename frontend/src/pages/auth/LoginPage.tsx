import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Package, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // TODO: Replace with actual API call
      // const { data } = await axios.post('/api/v1/auth/login', { email, password })
      // login(data.access_token, data.user)

      // Mock login for now
      login('demo-token', {
        id: '1',
        email,
        seller_id: 'demo-seller',
        marketplace_id: 'ARBP9OOSHTCHU',
        region: 'EU',
      })

      toast.success('تم تسجيل الدخول بنجاح')
      navigate('/dashboard')
    } catch (error) {
      toast.error('فشل تسجيل الدخول')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amazon-blue to-amazon-dark flex items-center justify-center p-4" dir="rtl">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-amazon-orange rounded-2xl mb-4">
            <Package className="w-8 h-8 text-amazon-dark" />
          </div>
          <h1 className="text-3xl font-bold text-white">Crazy Lister</h1>
          <p className="text-gray-400 mt-2">Amazon Auto-Listing System</p>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-2xl p-8 shadow-xl">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">تسجيل الدخول</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                البريد الإلكتروني
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange focus:border-amazon-orange transition-colors"
                placeholder="example@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                كلمة المرور
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange focus:border-amazon-orange transition-colors"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  جاري تسجيل الدخول...
                </>
              ) : (
                'تسجيل الدخول'
              )}
            </button>
          </form>

          <p className="text-center text-sm text-gray-600 mt-6">
            ليس لديك حساب؟{' '}
            <Link to="/register" className="text-amazon-orange font-semibold hover:underline">
              إنشاء حساب
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
