import { useState } from 'react'
import AuthMethodSelector from '@/components/auth/AuthMethodSelector'
import { useSessionStatus, useVerifySession, useLogout } from '@/api/hooks'
import { Shield, CheckCircle, AlertCircle, Loader2, LogOut, RefreshCw, Cloud } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { data: session, isLoading, refetch } = useSessionStatus()
  const verifyMutation = useVerifySession()
  const logoutMutation = useLogout()
  const [showAuthSelector, setShowAuthSelector] = useState(!session?.is_connected)

  const isConnected = session?.is_connected ?? false
  const isVerifying = verifyMutation.isPending
  const isLoggingOut = logoutMutation.isPending

  const handleVerify = async () => {
    try {
      await verifyMutation.mutateAsync()
      await refetch()
      toast.success('تم التحقق من الاتصال')
    } catch {
      toast.error('فشل التحقق - قد تكون الجلسة منتهية')
    }
  }

  const handleLogout = async () => {
    try {
      await logoutMutation.mutateAsync()
      await refetch()
      setShowAuthSelector(true)
      toast.success('تم تسجيل الخروج')
    } catch {
      toast.error('فشل تسجيل الخروج')
    }
  }

  const handleAuthSuccess = async () => {
    await refetch()
    setShowAuthSelector(false)
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
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Cloud className="w-7 h-7 text-amazon-orange" />
          الاتصال بـ Amazon
        </h1>
        <p className="text-gray-400 mt-1">اختر طريقة الاتصال المناسبة لك</p>
      </div>

      {/* Connection Status Banner */}
      {isConnected && (
        <div className={`p-4 rounded-xl border flex items-center justify-between ${
          session?.is_valid
            ? 'bg-green-500/10 border-green-500/30'
            : 'bg-yellow-500/10 border-yellow-500/30'
        }`}>
          <div className="flex items-center gap-3">
            {session?.is_valid
              ? <CheckCircle className="w-6 h-6 text-green-500" />
              : <AlertCircle className="w-6 h-6 text-yellow-500" />
            }
            <div>
              <h3 className={`font-bold ${
                session?.is_valid ? 'text-green-400' : 'text-yellow-400'
              }`}>
                {session?.is_valid ? 'متصل بـ Amazon' : 'متصل - الجلسة قد تكون منتهية'}
              </h3>
              <p className="text-xs text-gray-400">
                {session?.auth_method === 'browser'
                  ? `Browser Login - ${session.seller_name || session.email}`
                  : `SP-API - ${session.marketplace_id || ''}`
                }
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleVerify}
              disabled={isVerifying}
              className="flex items-center gap-1 px-3 py-2 text-sm bg-white/10 hover:bg-white/20 rounded-lg transition disabled:opacity-50"
            >
              {isVerifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              تحقق
            </button>
            <button
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="flex items-center gap-1 px-3 py-2 text-sm bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition disabled:opacity-50"
            >
              {isLoggingOut ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogOut className="w-4 h-4" />}
              خروج
            </button>
          </div>
        </div>
      )}

      {/* Auth Method Selector or Connected Info */}
      {showAuthSelector && !isConnected ? (
        <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6">
          <AuthMethodSelector onSuccess={handleAuthSuccess} />
        </div>
      ) : isConnected ? (
        /* Connected - Show Details */
        <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-6 h-6 text-green-400" />
            <h3 className="text-white font-bold text-lg">تفاصيل الاتصال</h3>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#0a0a0f] p-4 rounded-lg border border-gray-800">
              <span className="text-xs text-gray-500 block">طريقة الاتصال</span>
              <span className="text-white font-medium">
                {session?.auth_method === 'browser' ? '🌐 Browser Login' : '🔑 SP-API'}
              </span>
            </div>
            <div className="bg-[#0a0a0f] p-4 rounded-lg border border-gray-800">
              <span className="text-xs text-gray-500 block">
                {session?.auth_method === 'browser' ? 'البريد الإلكتروني' : 'Marketplace ID'}
              </span>
              <span className="text-white font-mono text-sm">
                {session?.auth_method === 'browser'
                  ? session?.email || '---'
                  : session?.marketplace_id || '---'
                }
              </span>
            </div>
            <div className="bg-[#0a0a0f] p-4 rounded-lg border border-gray-800">
              <span className="text-xs text-gray-500 block">اسم البائع</span>
              <span className="text-white text-sm">{session?.seller_name || '---'}</span>
            </div>
            {session?.auth_method === 'browser' && (
              <div className="bg-[#0a0a0f] p-4 rounded-lg border border-gray-800">
                <span className="text-xs text-gray-500 block">الدولة</span>
                <span className="text-white text-sm uppercase">{session?.country_code || '---'}</span>
              </div>
            )}
          </div>

          {session?.last_verified_at && (
            <div className="text-xs text-gray-500 pt-2 border-t border-gray-800">
              آخر تحقق: {new Date(session.last_verified_at).toLocaleString('ar-EG')}
            </div>
          )}

          <button
            onClick={() => setShowAuthSelector(true)}
            className="w-full py-3 border border-gray-700 rounded-lg text-gray-400 hover:text-white hover:border-amazon-orange transition"
          >
            تغيير طريقة الاتصال
          </button>
        </div>
      ) : null}
    </div>
  )
}
