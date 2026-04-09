import { Link } from 'react-router-dom'
import { Plus, Search, Filter } from 'lucide-react'

export default function ProductListPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">المنتجات</h1>
          <p className="text-gray-600 mt-1">إدارة كتالوج المنتجات</p>
        </div>
        <Link
          to="/products/create"
          className="flex items-center gap-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold px-6 py-3 rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5" />
          إضافة منتج
        </Link>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="بحث عن منتج..."
            className="w-full pr-10 pl-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange focus:border-amazon-orange"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter className="w-5 h-5" />
          تصفية
        </button>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">المنتج</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">SKU</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الفئة</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">السعر</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">إجراءات</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            <tr>
              <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                <p>لا توجد منتجات بعد</p>
                <Link to="/products/create" className="text-amazon-orange font-medium hover:underline mt-2 inline-block">
                  أضف أول منتج
                </Link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
