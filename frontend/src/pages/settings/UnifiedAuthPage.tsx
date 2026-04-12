import { useState } from 'react'
import { useSessionStatus, useLogout, useVerifySession, useDisconnectAmazon } from '@/api/hooks'
import { Shield, AlertTriangle, Loader2, CheckCircle, LogOut, RefreshCw, Mail } from 'lucide-react'
import AmazonLoginDirect from './AmazonLoginDirect'
import toast from 'react-hot-toast'

export default function UnifiedAuthPage() {
  const { data: session, isLoading, refetch } = useSessionStatus()
  const logoutMutation = useLogout()
  const verifyMutation = useVerifySession()
  const disconnectMutation = useDisconnectAmazon()

  const isConnected = session?.is_connected

  const handleLogout = async () => {
    await logoutMutation.mutateAsync()
    toast.success('تم تسجيل الخروج')
    refetch()
  }

  const handleDisconnect = async () => {
    if (session?.email) {
      await disconnectMutation.mutateAsync(session.email)
      toast.success('تم قطع الاتصال')
      refetch()
    }
  }

  const handleVerify = async () => {
    try {
      const result = await verifyMutation.mutateAsync()
      if (result.is_valid) {
        toast.success('الجلسة صالحة ✅')
      } else {
        toast.error('الجلسة انتهت - سجل الدخول مرة أخرى')
      }
    } catch {
      toast.error('فشل التحقق')
    }
    refetch()
  }

  const handleLoginSuccess = () => {
    refetch()
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-amazon-orange animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto" dir="rtl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">🔐 تسجيل الدخول بـ Amazon</h1>
        <p className="text-gray-400 mt-1">سجل دخولك مباشرة عبر Amazon Seller Central</p>
      </div>

      {/* Connection Status Banner */}
      {isConnected ? (
        <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-green-500" />
              <div>
                <h3 className="text-green-400 font-bold">
                  ✅ متصل ({session?.auth_method === 'browser' ? 'Browser' : 'SP-API'})
                </h3>
                <p className="text-xs text-gray-400">
                  {session?.email || session?.seller_name}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleVerify}
                disabled={verifyMutation.isPending}
                className="px-3 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-300 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${verifyMutation.isPending ? 'animate-spin' : ''}`} />
                تحقق
              </button>
              <button
                onClick={handleDisconnect}
                disabled={disconnectMutation.isPending}
                className="px-3 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
              >
                <LogOut className="w-4 h-4" />
                قطع
              </button>
              <button
                onClick={handleLogout}
                disabled={logoutMutation.isPending}
                className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
              >
                <LogOut className="w-4 h-4" />
                خروج
              </button>
            </div>
          </div>
          <div className="mt-3 bg-gray-800/50 rounded-lg p-3">
            <p className="text-gray-400 text-xs">
              🔒 متصل بنجاح. يمكنك استخدام باقي النظام الآن.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <div>
            <h3 className="text-red-400 font-bold">غير متصل</h3>
            <p className="text-xs text-gray-400">سجل دخولك عبر Amazon للمتابعة</p>
          </div>
        </div>
      )}

      {/* Login Form - only show if not connected */}
      {!isConnected && <LoginForm onSuccess={handleLoginSuccess} />}
    </div>
  )
}

function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('')
  const [countryCode, setCountryCode] = useState('eg')

  return (
    <div className="space-y-6">
      {/* Important notice */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 flex items-start gap-3">
        <Shield className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="text-blue-300 font-bold text-sm mb-1">ℹ️ تسجيل الدخول المباشر</h3>
          <p className="text-blue-300/70 text-xs leading-relaxed">
            سيتم فتح صفحة Amazon Seller Central في نافذة جديدة.
            <br />
            أدخل بياناتك مباشرة وسيتم الاتصال تلقائياً.
          </p>
        </div>
      </div>

      {/* Email & Country Input */}
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-4">
        <h3 className="text-white font-bold flex items-center gap-2">
          <Mail className="w-5 h-5 text-amazon-orange" />
          بيانات الحساب
        </h3>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            البريد الإلكتروني
          </label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="seller@example.com"
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-amazon-orange outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            الدولة
          </label>
          <select
            value={countryCode}
            onChange={e => setCountryCode(e.target.value)}
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-amazon-orange outline-none"
          >
            <option value="eg">🇪🇬 مصر</option>
            <option value="sa">🇸🇦 السعودية</option>
            <option value="ae">🇦🇪 الإمارات</option>
            <option value="uk">🇬🇧 المملكة المتحدة</option>
            <option value="us">🇺🇸 الولايات المتحدة</option>
          </select>
        </div>

        {/* Amazon Login Direct - Backend opens PyWebView window */}
        <AmazonLoginDirect
          country_code={countryCode}
          onSuccess={onSuccess}
        />
      </div>
    </div>
  )
}
