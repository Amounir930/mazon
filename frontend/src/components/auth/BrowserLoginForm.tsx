import { useState } from 'react'
import { useBrowserLogin, useSubmitOtp } from '@/api/hooks'
import { Shield, Loader2, AlertTriangle, Globe, Key, Mail } from 'lucide-react'
import toast from 'react-hot-toast'

interface BrowserLoginFormProps {
  onSuccess?: () => void
}

const COUNTRIES = [
  { code: 'us', label: '🇺🇸 أمريكا (US)', domain: 'amazon.com' },
  { code: 'uk', label: '🇬🇧 بريطانيا (UK)', domain: 'amazon.co.uk' },
  { code: 'ae', label: '🇦🇪 الإمارات (UAE)', domain: 'amazon.ae' },
  { code: 'sa', label: '🇸🇦 السعودية (KSA)', domain: 'amazon.sa' },
  { code: 'eg', label: '🇪🇬 مصر (Egypt)', domain: 'amazon.eg' },
  { code: 'de', label: '🇩🇪 ألمانيا (Germany)', domain: 'amazon.de' },
  { code: 'fr', label: '🇫🇷 فرنسا (France)', domain: 'amazon.fr' },
  { code: 'it', label: '🇮🇹 إيطاليا (Italy)', domain: 'amazon.it' },
  { code: 'es', label: '🇪🇸 إسبانيا (Spain)', domain: 'amazon.es' },
  { code: 'in', label: '🇮🇳 الهند (India)', domain: 'amazon.in' },
  { code: 'jp', label: '🇯🇵 اليابان (Japan)', domain: 'amazon.co.jp' },
  { code: 'ca', label: '🇨🇦 كندا (Canada)', domain: 'amazon.ca' },
]

export default function BrowserLoginForm({ onSuccess }: BrowserLoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [countryCode, setCountryCode] = useState('us')
  const [otp, setOtp] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [showWarning, setShowWarning] = useState(true)

  const loginMutation = useBrowserLogin()
  const otpMutation = useSubmitOtp()

  const isLoading = loginMutation.isPending || otpMutation.isPending
  const waitingForOtp = sessionId !== null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!email || !password) {
      toast.error('يرجى إدخال البريد الإلكتروني وكلمة المرور')
      return
    }

    try {
      const result = await loginMutation.mutateAsync({
        email,
        password,
        country_code: countryCode,
      })

      if (result.needs_otp && result.session_id) {
        setSessionId(result.session_id)
        toast.info('تم فتح المتصفح - يرجى إكمال تسجيل الدخول، أو أدخل OTP إذا طُلب')
        return
      }

      if (result.success) {
        toast.success(`تم الاتصال بنجاح! مرحباً ${result.seller_name || email}`)
        onSuccess?.()
      } else {
        toast.error(result.error || 'فشل تسجيل الدخول')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'حدث خطأ غير متوقع')
    }
  }

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!otp || !sessionId) return

    try {
      const result = await otpMutation.mutateAsync({ session_id: sessionId, otp })

      if (result.success) {
        toast.success('تم الاتصال بنجاح!')
        setSessionId(null)
        setOtp('')
        onSuccess?.()
      } else {
        toast.error(result.error || 'OTP غير صحيح')
      }
    } catch (error: any) {
      toast.error('حدث خطأ في التحقق من OTP')
    }
  }

  // Security warning
  if (showWarning) {
    return (
      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6 space-y-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h3 className="text-yellow-400 font-bold text-lg mb-2">تنبيه أمني مهم</h3>
            <ul className="text-yellow-200/80 text-sm space-y-1 list-disc list-inside">
              <li>سيتم فتح متصفح Chromium معزول على جهازك</li>
              <li>سيتم إدخال بياناتك تلقائياً في صفحة Amazon الرسمية</li>
              <li>لن يتم تخزين كلمة المرور - فقط الكوكيز مشفرة</li>
              <li>إذا كان حسابك يطلب OTP، ستحتاج لإدخاله</li>
              <li>هذه الطريقة قد تنتهك شروط Amazon - استخدمها على مسؤوليتك</li>
            </ul>
          </div>
        </div>
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => setShowWarning(false)}
            className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-3 rounded-lg transition"
          >
            فهمت - أكمل
          </button>
          <button
            onClick={() => setShowWarning(false)}
            className="px-6 py-3 border border-yellow-500/30 text-yellow-400 rounded-lg hover:bg-yellow-500/10 transition"
          >
            إلغاء
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Method Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
          <Globe className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h3 className="text-white font-bold">تسجيل الدخول عبر المتصفح</h3>
          <p className="text-gray-400 text-xs">سريع ~30 ثانية • يحتاج Email + Password</p>
        </div>
      </div>

      {waitingForOtp ? (
        /* OTP Form */
        <form onSubmit={handleOtpSubmit} className="space-y-4">
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <p className="text-blue-300 text-sm">
              🔐 تم فتح المتصفح. إذا ظهر طلب رمز OTP، أدخله هنا:
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              رمز التحقق (OTP)
            </label>
            <div className="relative">
              <Key className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={otp}
                onChange={e => setOtp(e.target.value)}
                className="w-full pr-10 pl-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white text-center text-xl tracking-widest focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="123456"
                maxLength={8}
                autoFocus
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isLoading || !otp}
              className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  جاري التحقق...
                </>
              ) : (
                'تحقق من OTP'
              )}
            </button>
            <button
              type="button"
              onClick={() => { setSessionId(null); setOtp('') }}
              className="px-4 py-3 border border-gray-700 rounded-lg text-gray-400 hover:text-white transition"
            >
              إلغاء
            </button>
          </div>
        </form>
      ) : (
        /* Login Form */
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
              <Mail className="w-4 h-4" /> البريد الإلكتروني
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
              placeholder="seller@example.com"
              autoComplete="email"
              disabled={isLoading}
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">كلمة المرور</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
              placeholder="••••••••"
              autoComplete="current-password"
              disabled={isLoading}
            />
          </div>

          {/* Country */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">الدولة / Marketplace</label>
            <select
              value={countryCode}
              onChange={e => setCountryCode(e.target.value)}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
              disabled={isLoading}
            >
              {COUNTRIES.map(c => (
                <option key={c.code} value={c.code}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2"
          >
            {isLoading ? (
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

          <p className="text-xs text-gray-500 text-center">
            سيتم فتح Chromium معزول • يُحفظ الكوكيز فقط (مشفر)
          </p>
        </form>
      )}
    </div>
  )
}
