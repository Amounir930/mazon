import { Link } from 'react-router-dom'
import { Package } from 'lucide-react'

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-amazon-blue to-amazon-dark flex items-center justify-center p-4" dir="rtl">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-amazon-orange rounded-2xl mb-4">
            <Package className="w-8 h-8 text-amazon-dark" />
          </div>
          <h1 className="text-3xl font-bold text-white">Crazy Lister</h1>
          <p className="text-gray-400 mt-2">إنشاء حساب جديد</p>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-xl">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">إنشاء حساب</h2>
          <p className="text-gray-600 text-center mb-6">
            سيتم تحويلك إلى صفحة تسجيل الدخول مع Amazon لتفويض الحساب.
          </p>

          <Link
            to="/login"
            className="block w-full bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold py-3 rounded-lg text-center transition-colors"
          >
            الذهاب لتسجيل الدخول
          </Link>

          <p className="text-center text-sm text-gray-600 mt-6">
            لديك حساب بالفعل؟{' '}
            <Link to="/login" className="text-amazon-orange font-semibold hover:underline">
              تسجيل الدخول
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
