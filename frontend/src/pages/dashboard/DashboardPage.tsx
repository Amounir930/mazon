import { useEffect, useState } from 'react'
import { Package, Upload, CheckCircle, XCircle, TrendingUp, Loader2, Plus, FileSpreadsheet, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useListings, useProducts } from '@/api/hooks'
import type { Listing } from '@/types/api'

export default function DashboardPage() {
  const { data: productsData, isLoading: loadingProducts } = useProducts({ page_size: 1 })
  const { data: listings, isLoading: loadingListings } = useListings()

  const totalProducts = productsData?.total ?? 0
  const totalListings = listings?.length ?? 0
  const published = listings?.filter((l: Listing) => l.status === 'success').length ?? 0
  const queued = listings?.filter((l: Listing) => l.status === 'queued' || l.status === 'processing').length ?? 0
  const failed = listings?.filter((l: Listing) => l.status === 'failed').length ?? 0

  const isLoading = loadingProducts || loadingListings

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    )
  }

  const stats = [
    { label: 'المنتجات', value: totalProducts.toString(), icon: Package, color: 'bg-blue-500' },
    { label: 'في الطابور', value: queued.toString(), icon: Upload, color: 'bg-yellow-500' },
    { label: 'منشورة', value: published.toString(), icon: CheckCircle, color: 'bg-green-500' },
    { label: 'فاشلة', value: failed.toString(), icon: XCircle, color: 'bg-red-500' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">لوحة التحكم</h1>
          <p className="text-gray-400 mt-1">مرحباً بك في نظام رفع المنتجات الآلي</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-400 rounded-lg border border-green-500/20">
          <TrendingUp className="w-5 h-5" />
          <span className="font-medium">{totalListings} عملية رفع</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-[#12121a] rounded-xl p-6 border border-gray-800/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">{label}</p>
                <p className="text-3xl font-bold text-white mt-1">{value}</p>
              </div>
              <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <h2 className="text-lg font-semibold text-white mt-8 mb-4">إجراءات سريعة</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/products/create"
          className="bg-[#12121a] rounded-xl p-6 border border-gray-800/50 hover:border-orange-500/50 transition-colors group"
        >
          <Plus className="w-8 h-8 text-orange-500 mb-3" />
          <h3 className="text-lg font-semibold text-white mb-2">إضافة منتج جديد</h3>
          <p className="text-gray-400 text-sm">أدخل بيانات المنتج وارفعه على أمازون</p>
        </Link>

        <Link
          to="/products/create"
          className="bg-[#12121a] rounded-xl p-6 border border-gray-800/50 hover:border-orange-500/50 transition-colors group"
        >
          <FileSpreadsheet className="w-8 h-8 text-blue-500 mb-3" />
          <h3 className="text-lg font-semibold text-white mb-2">رفع جماعي</h3>
          <p className="text-gray-400 text-sm">ارفع ملف CSV أو Excel لمنتجات متعددة</p>
        </Link>

        <Link
          to="/listings"
          className="bg-[#12121a] rounded-xl p-6 border border-gray-800/50 hover:border-orange-500/50 transition-colors group"
        >
          <RefreshCw className="w-8 h-8 text-green-500 mb-3" />
          <h3 className="text-lg font-semibold text-white mb-2">طابور الرفع</h3>
          <p className="text-gray-400 text-sm">تابع حالة رفع المنتجات لأمازون</p>
        </Link>
      </div>
    </div>
  )
}
