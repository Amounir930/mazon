import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter, Edit2, Trash2, Upload, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useProducts } from '@/api/hooks'
import { StatusBadge } from '@/components/common/StatusBadge'
import type { Product } from '@/types/api'

export default function ProductListPage() {
  const { user } = useAuth()
  const [search, setSearch] = useState('')
  const { data, isLoading, isError } = useProducts({
    seller_id: user?.seller_id || '',
    page: 1,
  })

  const filteredProducts = data?.items.filter(
    (p: Product) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">حدث خطأ في تحميل البيانات</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">المنتجات</h1>
          <p className="text-gray-600 mt-1">إدارة كتالوج المنتجات ({data?.total ?? 0})</p>
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
            value={search}
            onChange={(e) => setSearch(e.target.value)}
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
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الكمية</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">إجراءات</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredProducts?.map((product: Product) => (
              <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <p className="font-medium text-gray-800">{product.name}</p>
                  <p className="text-sm text-gray-500">{product.brand}</p>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 font-mono">{product.sku}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{product.category}</td>
                <td className="px-6 py-4 text-sm font-semibold text-gray-800">
                  {product.price.toFixed(2)} ج.م
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{product.quantity}</td>
                <td className="px-6 py-4">
                  <StatusBadge status={product.status} />
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <button className="p-2 text-gray-600 hover:text-amazon-orange hover:bg-orange-50 rounded-lg transition-colors">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors">
                      <Upload className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!filteredProducts || filteredProducts.length === 0) && (
          <div className="text-center py-12 text-gray-500">
            <p>لا توجد منتجات</p>
            <Link to="/products/create" className="text-amazon-orange font-medium hover:underline mt-2 inline-block">
              أضف أول منتج
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
