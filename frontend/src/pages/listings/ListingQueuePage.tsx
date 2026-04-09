import { Loader2, Play, RotateCcw } from 'lucide-react'
import { useListings } from '@/api/hooks'
import { StatusBadge } from '@/components/common/StatusBadge'
import type { Listing } from '@/types/api'

export default function ListingQueuePage() {
  const { data: listings, isLoading } = useListings({})

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">طابور الرفع</h1>
          <p className="text-gray-600 mt-1">متابعة حالة رفع المنتجات لأمازون ({listings?.length ?? 0})</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold rounded-lg transition-colors">
            <Play className="w-4 h-4" />
            رفع الكل
          </button>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            <RotateCcw className="w-4 h-4" />
            تحديث
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">#</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">المنتج</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">Feed ID</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الوقت</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">إجراء</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {listings?.map((listing: Listing, idx: number) => (
              <tr key={listing.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm text-gray-600">{idx + 1}</td>
                <td className="px-6 py-4 text-sm text-gray-800 font-medium">
                  {listing.product_id?.slice(0, 8)}...
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={listing.status} />
                </td>
                <td className="px-6 py-4 text-sm font-mono text-gray-600">
                  {listing.feed_submission_id || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {listing.created_at ? new Date(listing.created_at).toLocaleTimeString('ar-EG') : '-'}
                </td>
                <td className="px-6 py-4">
                  {listing.status === 'failed' && (
                    <button className="p-2 text-gray-600 hover:text-amazon-orange hover:bg-orange-50 rounded-lg transition-colors">
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!listings || listings.length === 0) && (
          <div className="text-center py-12 text-gray-500">
            <p>الطابور فارغ</p>
            <p className="text-sm text-gray-400 mt-2">أضف منتجات من صفحة المنتجات لبدء الرفع الآلي</p>
          </div>
        )}
      </div>

      {/* Stats */}
      {listings && listings.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-green-700">
              {listings.filter((l: Listing) => l.status === 'success').length}
            </p>
            <p className="text-sm text-green-600">نجح</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-yellow-700">
              {listings.filter((l: Listing) => l.status === 'queued').length}
            </p>
            <p className="text-sm text-yellow-600">في الطابور</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-blue-700">
              {listings.filter((l: Listing) => l.status === 'processing' || l.status === 'submitted').length}
            </p>
            <p className="text-sm text-blue-600">قيد المعالجة</p>
          </div>
          <div className="bg-red-50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-red-700">
              {listings.filter((l: Listing) => l.status === 'failed').length}
            </p>
            <p className="text-sm text-red-600">فشل</p>
          </div>
        </div>
      )}
    </div>
  )
}
