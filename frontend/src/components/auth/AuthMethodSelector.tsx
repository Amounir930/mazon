import { useState } from 'react'
import { Shield, Key, Globe, AlertTriangle, Loader2, CheckCircle } from 'lucide-react'
import { useBrowserLogin, useSubmitOtp, useSpapiLogin, useSessionStatus } from '@/api/hooks'
import toast from 'react-hot-toast'

const COUNTRIES = [
  { code: 'us', label: 'أمريكا', flag: '🇺🇸' },
  { code: 'uk', label: 'بريطانيا', flag: '🇬🇧' },
  { code: 'ae', label: 'الإمارات', flag: '🇦🇪' },
  { code: 'sa', label: 'السعودية', flag: '🇸🇦' },
  { code: 'eg', label: 'مصر', flag: '🇪🇬' },
  { code: 'de', label: 'ألمانيا', flag: '🇩🇪' },
  { code: 'fr', label: 'فرنسا', flag: '🇫🇷' },
  { code: 'it', label: 'إيطاليا', flag: '🇮🇹' },
  { code: 'es', label: 'إسبانيا', flag: '🇪🇸' },
  { code: 'jp', label: 'اليابان', flag: '🇯🇵' },
  { code: 'au', label: 'أستراليا', flag: '🇦🇺' },
]

export default function AuthMethodSelector() {
  const [method, setMethod] = useState<'browser' | 'spapi'>('browser')
  const { refetch: refetchSession } = useSessionStatus()

  return (
    <div className="space-y-6" dir="rtl">
      {/* اختيار الطريقة */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => setMethod('browser')}
          className={`p-6 rounded-xl border-2 transition-all text-right ${
            method === 'browser'
              ? 'border-orange-500 bg-orange-500/10'
              : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
          }`}
        >
          <Globe className={`w-8 h-8 mb-3 ${method === 'browser' ? 'text-orange-500' : 'text-gray-400'}`} />
          <h3 className="text-white font-bold text-lg mb-1">تسجيل عبر المتصفح</h3>
          <p className="text-gray-400 text-sm">⚡ سريع - 30 ثانية</p>
          <p className="text-gray-500 text-xs mt-2">Email + Password + OTP (لو مطلوب)</p>
        </button>

        <button
          onClick={() => setMethod('spapi')}
          className={`p-6 rounded-xl border-2 transition-all text-right ${
            method === 'spapi'
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
          }`}
        >
          <Key className={`w-8 h-8 mb-3 ${method === 'spapi' ? 'text-blue-500' : 'text-gray-400'}`} />
          <h3 className="text-white font-bold text-lg mb-1">SP-API (الرسمية)</h3>
          <p className="text-gray-400 text-sm">🔒 آمنة 100%</p>
          <p className="text-gray-500 text-xs mt-2">LWA Credentials + IAM Setup</p>
        </button>
      </div>

      {/* الفورم المناسب */}
      {method === 'browser' ? <BrowserLoginForm onSuccess={() => refetchSession()} /> : <SpapiLoginForm onSuccess={() => refetchSession()} />}
    </div>
  )
}

function BrowserLoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [countryCode, setCountryCode] = useState('us')
  const [otp, setOtp] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [showWarning, setShowWarning] = useState(true)

  const loginMutation = useBrowserLogin()
  const otpMutation = useSubmitOtp()

  const handleLogin = async () => {
    if (!email || !password) {
      toast.error('يرجى إدخال البريد الإلكتروني وكلمة المرور')
      return
    }

    const result = await loginMutation.mutateAsync({ email, password, country_code: countryCode })

    if (result.needs_otp) {
      setSessionId(result.session_id || null)
      toast.info('OTP مطلوب - أدخل رمز التحقق')
    } else if (result.success) {
      toast.success(`تم الاتصال بنجاح! (${result.seller_name})`)
      onSuccess()
    } else {
      toast.error(result.error || 'فشل تسجيل الدخول')
    }
  }

  const handleOtpSubmit = async () => {
    if (!sessionId || !otp) {
      toast.error('يرجى إدخال رمز OTP')
      return
    }

    const result = await otpMutation.mutateAsync({ session_id: sessionId, otp })

    if (result.success) {
      toast.success(`تم الاتصال بنجاح! (${result.seller_name})`)
      onSuccess()
    } else {
      toast.error(result.error || 'OTP غير صحيح')
    }
  }

  if (showWarning) {
    return (
      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6 space-y-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-yellow-400 font-bold text-lg mb-2">⚠️ تنبيه أمني هام</h3>
            <p className="text-yellow-300/80 text-sm leading-relaxed">
              هذه الطريقة تفتح متصفح Chrome حقيقي وتسجل الدخول بحسابك على Amazon.
              <br />
              سيتم حفظ <strong>الكوكيز فقط</strong> (ليس الباسوورد) في قاعدة بيانات محلية مشفرة.
              <br />
              <strong>ننصح باستخدام SP-API</strong> للأمان الكامل.
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowWarning(false)}
            className="px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 rounded-lg transition"
          >
            فهمت - أكمل
          </button>
          <button
            onClick={() => setShowWarning(false)}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition"
          >
            استخدم SP-API بدلاً منها
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-4">
      <h3 className="text-white font-bold text-lg flex items-center gap-2">
        <Globe className="w-5 h-5 text-orange-500" />
        تسجيل عبر المتصفح
      </h3>

      {/* OTP Form (لو مطلوب) */}
      {sessionId ? (
        <div className="space-y-4">
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <p className="text-blue-300 text-sm">أدخل رمز OTP المرسل لجوالك</p>
          </div>
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="رمز OTP"
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white text-center text-2xl tracking-widest focus:border-blue-500 outline-none"
          />
          <button
            onClick={handleOtpSubmit}
            disabled={otpMutation.isPending}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {otpMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle className="w-5 h-5" />}
            تأكيد OTP
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">البريد الإلكتروني</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seller@example.com"
              className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-orange-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">كلمة المرور</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-orange-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">الدولة</label>
            <select
              value={countryCode}
              onChange={(e) => setCountryCode(e.target.value)}
              className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-orange-500 outline-none"
            >
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.flag} {c.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleLogin}
            disabled={loginMutation.isPending}
            className="w-full bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loginMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                جاري تسجيل الدخول...
              </>
            ) : (
              <>
                <Shield className="w-5 h-5" />
                تسجيل الدخول
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

function SpapiLoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [refreshToken, setRefreshToken] = useState('')
  const [marketplaceId, setMarketplaceId] = useState('ARBP9OOSHTCHU')

  const spapiMutation = useSpapiLogin()

  const handleLogin = async () => {
    if (!clientId || !clientSecret || !refreshToken) {
      toast.error('يرجى ملء جميع حقول SP-API')
      return
    }

    const result = await spapiMutation.mutateAsync({
      lwa_client_id: clientId,
      lwa_client_secret: clientSecret,
      refresh_token: refreshToken,
      marketplace_id: marketplaceId,
    })

    if (result.success) {
      toast.success('تم حفظ بيانات SP-API بنجاح!')
      onSuccess()
    } else {
      toast.error(result.error || 'فشل حفظ البيانات')
    }
  }

  return (
    <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-4">
      <h3 className="text-white font-bold text-lg flex items-center gap-2">
        <Key className="w-5 h-5 text-blue-500" />
        SP-API Credentials
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">LWA Client ID</label>
          <input
            type="text"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            placeholder="amzn1.application-oa2-client..."
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-blue-500 outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">LWA Client Secret</label>
          <input
            type="password"
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
            placeholder="••••••••"
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-blue-500 outline-none"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">Refresh Token</label>
        <input
          type="password"
          value={refreshToken}
          onChange={(e) => setRefreshToken(e.target.value)}
          placeholder="Atzr|IwEBI..."
          className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-blue-500 outline-none"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">Marketplace ID</label>
        <input
          type="text"
          value={marketplaceId}
          onChange={(e) => setMarketplaceId(e.target.value)}
          placeholder="ARBP9OOSHTCHU"
          className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-blue-500 outline-none"
        />
      </div>

      <button
        onClick={handleLogin}
        disabled={spapiMutation.isPending}
        className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {spapiMutation.isPending ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            جاري الحفظ...
          </>
        ) : (
          <>
            <Shield className="w-5 h-5" />
            حفظ البيانات
          </>
        )}
      </button>
    </div>
  )
}
