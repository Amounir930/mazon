import { useState, useCallback, useRef } from 'react'
import { useGetLoginUrl, useConnectWithCookies } from '@/api/hooks'
import { Loader2, ExternalLink, CheckCircle, AlertCircle, Globe } from 'lucide-react'
import toast from 'react-hot-toast'

interface AmazonLoginPopupProps {
  email: string
  onSuccess?: () => void
  country_code?: string
}

/**
 * AmazonLoginPopup
 * 
 * يفتح نافذة PyWebView لتسجيل الدخول لـ Amazon
 * يراقب الـ URL لحد ما يدخل، بعدين يقرأ الـ cookies
 * ويبعتها للـ Backend
 */
export default function AmazonLoginPopup({ email, onSuccess, country_code = 'eg' }: AmazonLoginPopupProps) {
  const [status, setStatus] = useState<'idle' | 'opening' | 'waiting' | 'extracting' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [progress, setProgress] = useState(0)
  const loginUrlMutation = useGetLoginUrl()
  const connectMutation = useConnectWithCookies()
  const monitorInterval = useRef<ReturnType<typeof setInterval> | null>(null)
  const popupRef = useRef<Window | null>(null)  // Store popup reference

  const handleStartLogin = useCallback(async () => {
    if (!email) {
      toast.error('يرجى إدخال البريد الإلكتروني أولاً')
      return
    }

    try {
      setStatus('opening')
      setProgress(10)

      // 1. احصل على رابط تسجيل الدخول
      const loginUrlResult = await loginUrlMutation.mutateAsync(country_code)
      setProgress(20)

      if (!loginUrlResult.success) {
        throw new Error('فشل في الحصول على رابط تسجيل الدخول')
      }

      // 2. افتح نافذة PyWebView
      const loginUrl = loginUrlResult.login_url
      const popupWidth = 500
      const popupHeight = 600
      
      // حساب الموقع عشان النافذة تكون في النص
      const left = window.screen.width / 2 - popupWidth / 2
      const top = window.screen.height / 2 - popupHeight / 2

      const popup = window.open(
        loginUrl,
        'AmazonLogin',
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},scrollbars=yes,resizable=yes`
      )

      if (!popup) {
        throw new Error('المتصفح منع النافذة المنبثقة - يرجى السماح النوافذ المنبثقة')
      }

      popupRef.current = popup  // Save reference

      setStatus('waiting')
      setProgress(30)

      // 3. راقب الـ URL لحد ما يدخل
      let checkCount = 0
      const maxChecks = 120 // 10 دقائق (كل 5 ثواني)
      
      monitorInterval.current = setInterval(() => {
        checkCount++
        setProgress(Math.min(30 + (checkCount / maxChecks) * 50, 80))

        try {
          // حاول التحقق من الـ URL
          const currentUrl = popup.location?.href || ''
          
          // لو راح لصفحة home أو dashboard - معناه نجح
          if (
            currentUrl.includes('/home') ||
            currentUrl.includes('/dashboard') ||
            currentUrl.includes('/inventory') ||
            !currentUrl.includes('/ap/signin')
          ) {
            if (checkCount > 2) { // منع الكشف السريع قبل ما يحمل
              handleLoginSuccess(popup, email, country_code)
            }
          }

          // لو عدينا الـ maxChecks - timeout
          if (checkCount >= maxChecks) {
            clearInterval(monitorInterval.current!)
            setStatus('error')
            setErrorMessage('انتهت المهلة - يرجى المحاولة مرة أخرى')
            popup.close()
          }
        } catch (e) {
          // Cross-origin error - طبيعي قبل ما يدخل
          // يعني لسه في صفحة Amazon (نفس الأصل)
        }
      }, 5000)

    } catch (error: any) {
      setStatus('error')
      setErrorMessage(error.message || 'حدث خطأ غير متوقع')
      toast.error(error.message || 'فشل تسجيل الدخول')
    }
  }, [email, country_code])

  const handleLoginSuccess = async (popup: Window, email: string, country_code: string) => {
    try {
      setStatus('extracting')
      setProgress(85)

      if (monitorInterval.current) {
        clearInterval(monitorInterval.current)
      }

      // 4. اقرأ الـ cookies من النافذة
      // Note: ده هيشتغل لو النافذة من نفس الأصل (same-origin)
      // لو Playwright/PyWebView بيستخدموا نفس الـ context، هيشتغل
      let cookiesText = ''
      try {
        // حاول قراءة document.cookie مباشرة
        const doc = popup.document
        cookiesText = doc.cookie || ''
      } catch (e) {
        // لو cross-origin، جرب طريقة بديلة
        // ممكن نستخدم postMessage من جانب النافذة
        console.warn('Could not read cookies directly, trying alternative method...')
        
        // هنا ممكن نضيف logic بديل
        // لكن في الوقت الحالي، نعتبر إن المستخدم هيدخل يدوياً
      }

      // 5. حول الـ cookies لصيغة قابلة للإرسال
      let cookies: Array<Record<string, any>> = []
      
      if (cookiesText) {
        cookies = cookiesText.split(';').map(cookie => {
          const [name, ...valueParts] = cookie.trim().split('=')
          return {
            name: name.trim(),
            value: valueParts.join('=').trim(),
            domain: '.amazon.' + country_code,
            path: '/',
          }
        }).filter(c => c.name && c.value)
      }

      if (cookies.length === 0) {
        // لو مفيش cookies، جرب طريقة بديلة
        // ممكن نطلب من الـ backend يقرأ الـ cookies من الـ PyWebView context
        console.warn('No cookies extracted, will rely on backend cookie extraction')
        
        // في الحالة دي، ممكن نستخدم API مختلف
        // لكن في الوقت الحالي، نعتبرها نجاح ونسيب الـ backend يتعامل معاها
        toast('جاري الاتصال...', { icon: 'ℹ️' })
      }

      setProgress(90)

      // 6. ابعت الـ cookies للـ Backend
      const result = await connectMutation.mutateAsync({
        email,
        cookies,
        country_code,
        seller_name: email.split('@')[0], // مؤقتاً
      })

      setProgress(100)

      if (result.success) {
        setStatus('success')
        toast.success(`تم الاتصال بنجاح! (${result.seller_name})`)
        
        // اقفل النافذة
        try {
          popup.close()
        } catch (e) {
          // ممكن النافذة مقفولة بالفعل
        }

        // نبّع الـ parent بنجاح العملية
        onSuccess?.()
      } else {
        throw new Error(result.error || 'فشل في حفظ الجلسة')
      }

    } catch (error: any) {
      setStatus('error')
      setErrorMessage(error.message || 'فشل في حفظ الجلسة')
      toast.error(error.message || 'فشل تسجيل الدخول')
      
      if (monitorInterval.current) {
        clearInterval(monitorInterval.current)
      }
    }
  }

  const handleCancel = () => {
    if (monitorInterval.current) {
      clearInterval(monitorInterval.current)
    }
    if (popupRef.current && !popupRef.current.closed) {
      try {
        popupRef.current.close()
      } catch (e) {
        // Ignore if can't close
      }
    }
    popupRef.current = null
    setStatus('idle')
    setProgress(0)
    setErrorMessage('')
  }

  return (
    <div className="space-y-4">
      {/* الحالة: idle */}
      {status === 'idle' && (
        <button
          onClick={handleStartLogin}
          disabled={!email}
          className="w-full bg-amazon-orange hover:bg-amazon-orange/90 text-white font-bold py-3 px-4 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Globe className="w-5 h-5" />
          تسجيل الدخول عبر Amazon
        </button>
      )}

      {/* الحالة: opening */}
      {status === 'opening' && (
        <div className="bg-[#1a1a2e] rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-amazon-orange animate-spin" />
            <span className="text-white text-sm">جاري فتح صفحة تسجيل الدخول...</span>
          </div>
          <ProgressBar progress={progress} />
        </div>
      )}

      {/* الحالة: waiting */}
      {status === 'waiting' && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3">
            <ExternalLink className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-2 flex-1">
              <p className="text-blue-300 font-medium text-sm">
                تم فتح صفحة Amazon في نافذة جديدة
              </p>
              <p className="text-blue-300/70 text-xs">
                يرجى إدخال بريدك الإلكتروني وكلمة المرور في النافذة المنبثقة.
                <br />
                <strong>بعد تسجيل الدخول بنجاح، اضغط الزر أدناه:</strong>
              </p>
            </div>
          </div>
          <ProgressBar progress={progress} />
          
          {/* زر fallback - المستخدم يضغطه لما يسجل دخول */}
          <button
            onClick={() => {
              if (monitorInterval.current) {
                clearInterval(monitorInterval.current)
              }
              // هنا بنفترض إن المستخدم سجل دخول بنجاح
              // بنحاول نقرأ الـ cookies من النافذة
              if (popupRef.current) {
                handleLoginSuccess(popupRef.current, email, country_code)
              }
            }}
            className="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 rounded-lg transition flex items-center justify-center gap-2"
          >
            <CheckCircle className="w-4 h-4" />
            ✅ تم تسجيل الدخول - اتصل الآن
          </button>
          
          <button
            onClick={handleCancel}
            className="w-full py-2 text-sm text-gray-400 hover:text-white transition"
          >
            إلغاء
          </button>
        </div>
      )}

      {/* الحالة: extracting */}
      {status === 'extracting' && (
        <div className="bg-[#1a1a2e] rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-amazon-orange animate-spin" />
            <span className="text-white text-sm">جاري استخراج البيانات والاتصال...</span>
          </div>
          <ProgressBar progress={progress} />
        </div>
      )}

      {/* الحالة: success */}
      {status === 'success' && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-green-300 font-medium">تم الاتصال بنجاح! ✅</span>
          </div>
        </div>
      )}

      {/* الحالة: error */}
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
            onClick={handleCancel}
            className="w-full py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm transition"
          >
            حاول مرة أخرى
          </button>
        </div>
      )}
    </div>
  )
}

function ProgressBar({ progress }: { progress: number }) {
  return (
    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
      <div
        className="h-full bg-amazon-orange transition-all duration-500 ease-out rounded-full"
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}
