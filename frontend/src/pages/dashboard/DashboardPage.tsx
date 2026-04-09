import { Package, Upload, CheckCircle, XCircle, TrendingUp, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useStats } from '@/api/hooks'
import { Link } from 'react-router-dom'

export default function DashboardPage() {
  const { sellerId } = useAuth()
  const { totalProducts, published, queued, failed, processing } = useStats(sellerId)

  const stats = [
    { label: 'المنتجات', value: totalProducts.toString(), icon: Package, color: 'bg-blue-500' },
    { label: 'في الطابور', value: queued.toString(), icon: Upload, color: 'bg-yellow-500' },
    { label: 'منشورة', value: published.toString(), icon: CheckCircle, color: 'bg-green-500' },
    { label: 'فاشلة', value: failed.toString(), icon: XCircle, color: 'bg-red-500' },
  ]

  if (!totalProducts && !published && !queued && !failed && !processing) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">لوحة التحكم</h1>
          <p className="text-gray-600 mt-1">مرحباً بك في نظام رفع المنتجات الآلي</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg">
          <TrendingUp className="w-5 h-5" />
          <span className="font-medium">{processing} قيد المعالجة</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{label}</p>
                <p className="text-3xl font-bold text-gray-800 mt-1">{value}</p>
              </div>
              <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          to="/products/create"
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:border-amazon-orange transition-colors group"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-2">إضافة منتج جديد</h3>
          <p className="text-gray-600 text-sm">أدخل بيانات المنتج وارفعه على أمازون</p>
          <p className="text-amazon-orange font-medium mt-4 group-hover:underline">ابدأ الآن ←</p>
        </Link>

        <Link
          to="/listings"
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:border-amazon-orange transition-colors group"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-2">طابور الرفع</h3>
          <p className="text-gray-600 text-sm">تابع حالة رفع المنتجات لأمازون</p>
          <p className="text-amazon-orange font-medium mt-4 group-hover:underline">عرض الطابور ←</p>
        </Link>
      </div>
    </div>
  )
}
