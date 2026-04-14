import { useState, useCallback } from 'react'
import { Loader2, CheckCircle, AlertCircle, Globe } from 'lucide-react'
import toast from 'react-hot-toast'

interface AmazonLoginDirectProps {
  email?: string
  onSuccess?: (result: any) => void
  country_code?: string
}

/**
 * AmazonLoginDirect - الطريقة الصح
 * 
 * بيبعت طلب للـ Backend → Backend بيفتح نافذة Amazon
 * المستخدم بيدخل → Backend بيقرا الـ cookies تلقائياً
 * من غير ما الـ Frontend يتدخل في قراءة الـ cookies
 */
export default function AmazonLoginDirect({ email, onSuccess, country_code = 'eg' }: AmazonLoginDirectProps) {
  const [status, setStatus] = useState<'idle' | 'opening' | 'waiting' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleStartLogin = useCallback(async () => {
    try {
      setStatus('opening')
      
      // نطلب من الـ Backend يفتح نافذة Amazon
      const response = await fetch(`/api/v1/auth/pywebview-login?country_code=${country_code}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      const result = await response.json()

      if (result.success) {
        setStatus('success')
        toast.success(`تم الاتصال بنجاح! (${result.seller_name})`)
        onSuccess?.(result)
      } else {
        setStatus('error')
        setErrorMessage(result.error || 'فشل تسجيل الدخول')
        toast.error(result.error || 'فشل تسجيل الدخول')
      }
    } catch (error: any) {
      setStatus('error')
      setErrorMessage(error.message || 'حدث خطأ غير متوقع')
      toast.error(error.message || 'فشل تسجيل الدخول')
    }
  }, [country_code, onSuccess])

  return (
    <div className="space-y-4">
      {status === 'idle' && (
        <button
          onClick={handleStartLogin}
          className="w-full bg-amazon-orange hover:bg-amazon-orange/90 text-white font-bold py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
        >
          <Globe className="w-5 h-5" />
          تسجيل الدخول عبر Amazon Seller Central
        </button>
      )}

      {status === 'opening' && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
            <div>
              <p className="text-blue-300 font-medium text-sm">جاري فتح نافذة تسجيل الدخول...</p>
              <p className="text-blue-300/70 text-xs mt-1">
                نافذة Amazon هتفتح. سجل دخولك (email + password + OTP لو مطلوب).
                <br />
                بعد ما تدخل، النافذة هتقفل تلقائياً والاتصال هيتم.
              </p>
            </div>
          </div>
        </div>
      )}

      {status === 'success' && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-green-300 font-medium">تم الاتصال بنجاح! ✅</span>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-red-300 font-medium text-sm">فشل تسجيل الدخول</p>
              <p className="text-red-300/70 text-xs mt-1">{errorMessage}</p>
            </div>
          </div>
          <button
            onClick={() => { setStatus('idle'); setErrorMessage('') }}
            className="w-full py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm transition"
          >
            حاول مرة أخرى
          </button>
        </div>
      )}
    </div>
  )
}
