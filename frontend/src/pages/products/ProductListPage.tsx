import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Filter, Edit2, Trash2, Upload, Loader2, RefreshCw, FileDown, ChevronDown } from 'lucide-react'
import { useProducts, useDeleteProduct, useSubmitListing, useSyncFromAmazon, useExportToAmazon, useExportPriceInventory, useExportListingLoader } from '@/api/hooks'
import { StatusBadge } from '@/components/common/StatusBadge'
import type { Product } from '@/types/api'
import toast from 'react-hot-toast'

export default function ProductListPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const { data, isLoading, isError, refetch } = useProducts({ page: 1, search: search || undefined })
  const deleteMutation = useDeleteProduct()
  const listMutation = useSubmitListing()
  const syncMutation = useSyncFromAmazon()
  const exportMutation = useExportToAmazon()
  const exportPriceMutation = useExportPriceInventory()
  const exportListingMutation = useExportListingLoader()

  // Backend handles search -- no client-side filtering needed
  const products = data?.items ?? []

  const handleDelete = async (id: string) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا المنتج؟')) return

    try {
      await deleteMutation.mutateAsync(id)
      toast.success('تم حذف المنتج بنجاح')
    } catch (error) {
      toast.error('فشل في حذف المنتج')
    }
  }

  const handleList = async (id: string) => {
    try {
      await listMutation.mutateAsync(id)
      toast.success('تم إرسال طلب الرفع للأمازون')
    } catch (error) {
      toast.error('فشل في إرسال طلب الرفع')
    }
  }

  const handleEdit = (product: Product) => {
    navigate('/products/create', { state: { editMode: true, editProduct: product } })
  }

  const handleSync = async () => {
    try {
      const result = await syncMutation.mutateAsync()
      toast.success(result.message || 'تمت المزامنة بنجاح')
      refetch()
    } catch (error: any) {
      const detail = error.response?.data?.detail
      let message = 'فشلت المزامنة'

      if (Array.isArray(detail)) {
        message = detail.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join('\n')
      } else if (typeof detail === 'string') {
        message = detail
      }

      toast.error(message)
    }
  }

  // Handle Import from Amazon (Amazon → Local DB)
  const handleImportFromAmazon = async () => {
    toast.error('هذه الميزة تحتاج تسجيل دخول كامل عبر Amazon SP-API. حالياً يمكنك إضافة المنتجات يدوياً.')
    return

    // Code below is disabled until proper authentication is available
    /*
    try {
      const result = await syncMutation.mutateAsync()
      toast.success(result.message || 'تمت المزامنة بنجاح')
      refetch()
    } catch (error: any) {
      const detail = error.response?.data?.detail
      let message = 'فشلت المزامنة'

      if (Array.isArray(detail)) {
        message = detail.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join('\n')
      } else if (typeof detail === 'string') {
        message = detail
      }

      toast.error(message)
    }
    */
  }

  // Handle Export to Amazon (Local DB → Amazon Listing)
  const handleExportToAmazon = async () => {
    try {
      const result = await exportMutation.mutateAsync()
      toast.success(result.message || 'تم رفع المنتجات إلى Amazon بنجاح')
      refetch()
    } catch (error: any) {
      const detail = error.response?.data?.detail
      let message = 'فشل الرفع إلى Amazon'

      if (Array.isArray(detail)) {
        message = detail.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join('\n')
      } else if (typeof detail === 'string') {
        message = detail
      }

      toast.error(message)
    }
  }

  const handleExportPriceInventory = async () => {
    try {
      await exportPriceMutation.mutateAsync()
      toast.success('تم تصدير ملف Price & Inventory بنجاح')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل التصدير')
    }
  }

  const handleExportListingLoader = async () => {
    try {
      await exportListingMutation.mutateAsync()
      toast.success('تم تصدير ملف Listing Loader بنجاح')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل التصدير')
    }
  }

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
          <h1 className="text-2xl font-bold text-white">المنتجات</h1>
          <p className="text-gray-400 mt-1">إدارة كتالوج المنتجات ({data?.total ?? 0})</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Export Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold px-4 py-3 rounded-lg transition-colors"
            >
              <FileDown className="w-5 h-5" />
              تصدير Excel
              <ChevronDown className="w-4 h-4" />
            </button>
            {showExportMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowExportMenu(false)} />
                <div className="absolute right-0 mt-2 w-64 bg-[#1a1a2e] border border-gray-700 rounded-lg shadow-xl z-20 overflow-hidden">
                  <button
                    onClick={() => { handleExportPriceInventory(); setShowExportMenu(false); }}
                    disabled={exportPriceMutation.isPending}
                    className="w-full px-4 py-3 text-right text-sm text-white hover:bg-gray-700 transition flex items-center justify-between gap-2 disabled:opacity-50"
                  >
                    {exportPriceMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                    <span>
                      <span className="font-medium">Price & Inventory</span>
                      <span className="text-gray-400 text-xs block">تحديث أسعار فقط</span>
                    </span>
                  </button>
                  <button
                    onClick={() => { handleExportListingLoader(); setShowExportMenu(false); }}
                    disabled={exportListingMutation.isPending}
                    className="w-full px-4 py-3 text-right text-sm text-white hover:bg-gray-700 transition flex items-center justify-between gap-2 border-t border-gray-700 disabled:opacity-50"
                  >
                    {exportListingMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                    <span>
                      <span className="font-medium">Listing Loader</span>
                      <span className="text-gray-400 text-xs block">إضافة عروض لمنتجات موجودة</span>
                    </span>
                  </button>
                </div>
              </>
            )}
          </div>

          <button
            onClick={handleExportToAmazon}
            disabled={exportMutation.isPending}
            className="flex items-center gap-2 bg-amazon-orange hover:bg-orange-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors disabled:opacity-50"
            title="رفع المنتجات من قاعدة البيانات إلى Amazon Listing"
          >
            {exportMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                جاري الرفع...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                تصدير لـ Amazon
              </>
            )}
          </button>

          <button
            onClick={handleImportFromAmazon}
            disabled={syncMutation.isPending}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors disabled:opacity-50"
            title="استيراد المنتجات من Amazon Seller Central"
          >
            {syncMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                جاري الاستيراد...
              </>
            ) : (
              <>
                <RefreshCw className="w-5 h-5" />
                استيراد من Amazon
              </>
            )}
          </button>
          <Link
            to="/products/create"
            className="flex items-center gap-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            إضافة منتج
          </Link>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث عن منتج... (اسم، SKU، الفئة)"
            className="w-full pr-10 pl-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange focus:border-amazon-orange"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter className="w-5 h-5" />
          تصفية
        </button>
      </div>

      {/* Products Table */}
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#1a1a2e]">
            <tr>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">المنتج</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">SKU</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">الفئة</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">السعر</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">الكمية</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">الحالة</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">إجراءات</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/50">
            {products.map((product: Product) => (
              <tr key={product.id} className="hover:bg-[#1a1a2e] transition-colors">
                <td className="px-6 py-4">
                  <p className="font-medium text-white">{product.name}</p>
                  <p className="text-sm text-gray-500">{product.brand}</p>
                </td>
                <td className="px-6 py-4 text-sm text-gray-400 font-mono">{product.sku}</td>
                <td className="px-6 py-4 text-sm text-gray-400">{product.category}</td>
                <td className="px-6 py-4 text-sm font-semibold text-orange-500">
                  {Number(product.price).toFixed(2)} ج.م
                </td>
                <td className="px-6 py-4 text-sm text-gray-400">{product.quantity}</td>
                <td className="px-6 py-4">
                  <StatusBadge status={product.status} />
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(product)}
                      className="p-2 text-gray-400 hover:text-orange-500 hover:bg-orange-500/10 rounded-lg transition-colors"
                      title="تعديل"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleList(product.id)}
                      disabled={listMutation.isPending}
                      className="p-2 text-gray-400 hover:text-green-500 hover:bg-green-500/10 rounded-lg transition-colors disabled:opacity-50"
                      title="رفع للأمازون"
                    >
                      {listMutation.isPending && listMutation.variables === product.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Upload className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(product.id)}
                      disabled={deleteMutation.isPending}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                      title="حذف"
                    >
                      {deleteMutation.isPending && deleteMutation.variables === product.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!products || products.length === 0) && (
          <div className="text-center py-12 text-gray-500">
            <p>لا توجد منتجات</p>
            <Link to="/products/create" className="text-orange-500 font-medium hover:underline mt-2 inline-block">
              أضف أول منتج
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
