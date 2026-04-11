import { useSessionStatus, useLogout, useVerifySession } from '@/api/hooks'
import AuthMethodSelector from '@/components/auth/AuthMethodSelector'
import { Shield, CheckCircle, AlertCircle, Loader2, LogOut, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { data: session, isLoading, refetch } = useSessionStatus()
  const logoutMutation = useLogout()
  const verifyMutation = useVerifySession()

  const isConnected = session?.is_connected

  const handleLogout = async () => {
    await logoutMutation.mutateAsync()
    toast.success('تم تسجيل الخروج')
    refetch()
  }

  const handleVerify = async () => {
    try {
      const result = await verifyMutation.mutateAsync()
      if (result.is_valid) {
        toast.success('الجلسة صالحة ✅')
      } else {
        toast.error('الجلسة انتهت - يرجى تسجيل الدخول مرة أخرى')
      }
    } catch {
      toast.error('فشل التحقق من الجلسة')
    }
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
    <div className="space-y-6 max-w-4xl mx-auto" dir="rtl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">🔐 إعدادات الاتصال بـ Amazon</h1>
        <p className="text-gray-400 mt-1">اختر طريقة تسجيل الدخول المناسبة لك</p>
      </div>

      {/* Connection Status Banner */}
      {isConnected && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-6 h-6 text-green-500" />
            <div>
              <h3 className="text-green-400 font-bold">
                متصل بـ Amazon ({session?.auth_method === 'browser' ? 'Browser Login' : 'SP-API'})
              </h3>
              <p className="text-xs text-gray-400">
                {session?.auth_method === 'browser'
                  ? `Email: ${session?.email} | Country: ${session?.country_code?.toUpperCase()}`
                  : `Marketplace: ${session?.marketplace_id}`}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleVerify}
              disabled={verifyMutation.isPending}
              className="px-3 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-300 rounded-lg flex items-center gap-2 transition text-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${verifyMutation.isPending ? 'animate-spin' : ''}`} />
              تحقق
            </button>
            <button
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
              className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg flex items-center gap-2 transition text-sm disabled:opacity-50"
            >
              <LogOut className="w-4 h-4" />
              خروج
            </button>
          </div>
        </div>
      )}

      {!isConnected && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle className="w-6 h-6 text-red-500" />
          <div>
            <h3 className="text-red-400 font-bold">غير متصل</h3>
            <p className="text-xs text-gray-400">يرجى تسجيل الدخول بإحدى الطرق أدناه</p>
          </div>
        </div>
      )}

      {/* Auth Method Selector & Forms */}
      <AuthMethodSelector />
    </div>
  )
}
