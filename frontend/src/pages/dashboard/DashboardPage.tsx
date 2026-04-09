import { Package, Upload, CheckCircle, XCircle, TrendingUp } from 'lucide-react'

const stats = [
  { label: 'المنتجات', value: '1,234', icon: Package, color: 'bg-blue-500' },
  { label: 'في الطابور', value: '56', icon: Upload, color: 'bg-yellow-500' },
  { label: 'منشورة', value: '1,178', icon: CheckCircle, color: 'bg-green-500' },
  { label: 'فاشلة', value: '12', icon: XCircle, color: 'bg-red-500' },
]

export default function DashboardPage() {
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
          <span className="font-medium">+12% هذا الأسبوع</span>
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

      {/* Recent Activity */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">آخر النشاطات</h2>
        <div className="text-center py-8 text-gray-500">
          <p>لا توجد نشاطات بعد</p>
          <p className="text-sm mt-2">ابدأ بإضافة منتج جديد من صفحة المنتجات</p>
        </div>
      </div>
    </div>
  )
}
