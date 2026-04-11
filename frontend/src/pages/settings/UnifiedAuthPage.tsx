import { useState } from 'react'
import { useSessionStatus, useBrowserLogin, useSubmitOtp, useSpapiLogin, useLogout, useVerifySession } from '@/api/hooks'
import { Shield, Key, Monitor, AlertTriangle, Loader2, CheckCircle, LogOut, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function UnifiedAuthPage() {
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
        toast.error('الجلسة انتهت - سجل الدخول مرة أخرى')
      }
    } catch {
      toast.error('فشل التحقق')
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
    <div className="space-y-6 max-w-3xl mx-auto" dir="rtl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">🔐 تسجيل الدخول بـ Amazon</h1>
        <p className="text-gray-400 mt-1">SP-API حقيقي - بدون بيانات وهمية</p>
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
                  {session?.email || session?.marketplace_id}
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
              🔒 الخانات مقفلة لأنك متصل بالفعل. سجل خروج لتغيير الطريقة.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <div>
            <h3 className="text-red-400 font-bold">غير متصل</h3>
            <p className="text-xs text-gray-400">اختر طريقة تسجيل الدخول أدناه</p>
          </div>
        </div>
      )}

      {/* Auth Methods - only show if not connected */}
      {!isConnected && <AuthMethods onConnect={() => refetch()} />}
    </div>
  )
}

function AuthMethods({ onConnect }: { onConnect: () => void }) {
  return (
    <div className="space-y-4">
      {/* Important notice */}
      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 flex items-start gap-3">
        <Shield className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="text-yellow-300 font-bold text-sm mb-1">⚠️ تسجيل المتصفح غير متاح حالياً</h3>
          <p className="text-yellow-300/70 text-xs leading-relaxed">
            نظراً لمشاكل توافق Playwright مع Windows/Uvicorn، استخدم
            <strong> SP-API credentials</strong> بدلاً منها.
          </p>
        </div>
      </div>

      {/* Only SP-API form */}
      <SpapiForm onSuccess={onConnect} />
    </div>
  )
}

function AutoForm({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const loginMutation = useBrowserLogin()
  const otpMutation = useSubmitOtp()

  const handleLogin = async () => {
    if (!email || !password) { toast.error('أدخل الإيميل والباسوورد'); return }
    const result = await loginMutation.mutateAsync({ email, password, country_code: 'eg' })
    if (result.needs_otp) {
      setSessionId(result.session_id || null)
      toast.info('OTP مطلوب')
    } else if (result.success) {
      toast.success(`تم الاتصال! (${result.seller_name})`)
      onSuccess()
    } else {
      toast.error(result.error || 'فشل تسجيل الدخول')
    }
  }

  const handleOtp = async () => {
    if (!sessionId || !otp) { toast.error('أدخل OTP'); return }
    const result = await otpMutation.mutateAsync({ session_id: sessionId, otp })
    if (result.success) {
      toast.success(`تم الاتصال! (${result.seller_name})`)
      onSuccess()
    } else {
      toast.error(result.error || 'OTP خطأ')
    }
  }

  return (
    <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-4">
      <h3 className="text-white font-bold flex items-center gap-2">
        <Monitor className="w-5 h-5 text-orange-500" />
        تسجيل مباشر عبر المتصفح
      </h3>

      {sessionId ? (
        <>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-blue-300 text-sm">
            أدخل رمز OTP المرسل لجوالك
          </div>
          <input
            type="text"
            value={otp}
            onChange={e => setOtp(e.target.value)}
            placeholder="رمز التحقق"
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white text-center text-2xl tracking-widest focus:border-blue-500 outline-none"
          />
          <SubmitBtn onClick={handleOtp} loading={otpMutation.isPending} label="تأكيد OTP" color="blue" />
        </>
      ) : (
        <>
          <Input label="البريد الإلكتروني" type="email" value={email} onChange={setEmail} placeholder="seller@example.com" />
          <Input label="كلمة المرور" type="password" value={password} onChange={setPassword} placeholder="••••••••" />
          <SubmitBtn onClick={handleLogin} loading={loginMutation.isPending} label="تسجيل الدخول" />
        </>
      )}
    </div>
  )
}

function SpapiForm({ onSuccess }: { onSuccess: () => void }) {
  const [form, setForm] = useState({ clientId: '', clientSecret: '', refreshToken: '', marketplaceId: 'ARBP9OOSHTCHU' })
  const mutation = useSpapiLogin()

  const handleSubmit = async () => {
    if (!form.clientId || !form.clientSecret || !form.refreshToken) {
      toast.error('يرجى ملء جميع الحقول')
      return
    }
    const result = await mutation.mutateAsync({
      lwa_client_id: form.clientId,
      lwa_client_secret: form.clientSecret,
      refresh_token: form.refreshToken,
      marketplace_id: form.marketplaceId,
    })
    if (result.success) {
      toast.success(`تم الاتصال! (${result.seller_name || 'SP-API'})`)
      onSuccess()
    } else {
      toast.error(result.error || 'فشل الاتصال')
    }
  }

  return (
    <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-4">
      <h3 className="text-white font-bold flex items-center gap-2">
        <Key className="w-5 h-5 text-blue-500" />
        SP-API Credentials
      </h3>
      <p className="text-gray-400 text-xs">
        احصل على هذه البيانات من{' '}
        <a href="https://developer.amazon.com" target="_blank" rel="noreferrer" className="text-blue-400 underline">
          Amazon Developer Console
        </a>
      </p>
      <Input label="LWA Client ID" value={form.clientId} onChange={v => setForm({...form, clientId: v})} placeholder="amzn1.application-oa2-client..." />
      <Input label="LWA Client Secret" type="password" value={form.clientSecret} onChange={v => setForm({...form, clientSecret: v})} placeholder="••••••••" />
      <Input label="Refresh Token" type="password" value={form.refreshToken} onChange={v => setForm({...form, refreshToken: v})} placeholder="Atzr|..." />
      <Input label="Marketplace ID" value={form.marketplaceId} onChange={v => setForm({...form, marketplaceId: v})} placeholder="ARBP9OOSHTCHU" />
      <SubmitBtn onClick={handleSubmit} loading={mutation.isPending} label="حفظ والاتصال" color="blue" />
    </div>
  )
}

function Input({ label, value, onChange, type = 'text', placeholder }: any) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-400 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-orange-500 outline-none"
      />
    </div>
  )
}

function SubmitBtn({ onClick, loading, label, color = 'orange' }: { onClick: () => void; loading?: boolean; label: string; color?: string }) {
  const colors: Record<string, string> = {
    orange: 'bg-orange-500 hover:bg-orange-600',
    blue: 'bg-blue-500 hover:bg-blue-600',
  }
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`w-full ${colors[color]} text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50`}
    >
      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle className="w-5 h-5" />}
      {label}
    </button>
  )
}
