import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search, Filter, Edit2, Trash2, Upload, Loader2, RefreshCw, FileDown, ChevronDown, FileSpreadsheet, X, Check, Download, AlertCircle, Image as ImageIcon, CloudOff, Cloud } from 'lucide-react'
import { useProducts, useDeleteProduct, useSubmitListing, useSyncFromAmazon, useExportToAmazon, useExportPriceInventory, useExportListingLoader, useDeleteListing, usePatchListing } from '@/api/hooks'
import { productsApi } from '@/api/endpoints'
import { StatusBadge } from '@/components/common/StatusBadge'
import type { Product } from '@/types/api'
import toast from 'react-hot-toast'
import {
  importExcelFile,
  generateTemplateExcel,
  type ParsedProduct,
  type ValidationError,
} from '@/services/excel_import_service'

export default function ProductListPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [showExportMenu, setShowExportMenu] = useState(false)

  // Excel import state
  const [showExcelModal, setShowExcelModal] = useState(false)
  const [excelProducts, setExcelProducts] = useState<ParsedProduct[]>([])
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [importing, setImporting] = useState(false)
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([])

  const { data, isLoading, isError, refetch } = useProducts({ page: 1, search: search || undefined })
  const deleteMutation = useDeleteProduct()
  const listMutation = useSubmitListing()
  const syncMutation = useSyncFromAmazon()
  const exportMutation = useExportToAmazon()
  const exportPriceMutation = useExportPriceInventory()
  const exportListingMutation = useExportListingLoader()

  // SP-API mutations (Amazon official)
  const deleteFromAmazonMutation = useDeleteListing()
  const patchAmazonMutation = usePatchListing()

  // Use ENV seller_id as default (from .env: A1DSHARRBRWYZW)
  const SELLER_ID = 'A1DSHARRBRWYZW'

  const handleDeleteFromAmazon = async (sku: string) => {
    if (!window.confirm(`هل أنت متأكد من حذف "${sku}" من Amazon؟ هذا الإجراء لا رجعة فيه.`)) return
    try {
      await deleteFromAmazonMutation.mutateAsync({ sellerId: SELLER_ID, sku })
      toast.success(`تم حذف ${sku} من Amazon`)
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'فشل الحذف من Amazon')
    }
  }

  const handleUpdatePriceOnAmazon = async (product: Product) => {
    const newPrice = prompt(`السعر الحالي: ${product.price} ج.م\nأدخل السعر الجديد:`, String(product.price))
    if (!newPrice || isNaN(Number(newPrice)) || Number(newPrice) <= 0) return

    try {
      await patchAmazonMutation.mutateAsync({
        sellerId: SELLER_ID,
        sku: product.sku,
        data: {
          product_type: product.product_type || 'HOME_ORGANIZERS_AND_STORAGE',
          patches: [
            {
              op: 'replace',
              path: '/attributes/purchasable_offer',
              value: [{
                our_price: [{ schedule: [{ value_with_tax: Number(newPrice) }] }],
                currency: 'EGP',
              }],
            },
          ],
        },
      })
      toast.success(`تم تحديث سعر ${product.sku} على Amazon`)
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'فشل تحديث السعر على Amazon')
    }
  }

  const handleUpdateQuantityOnAmazon = async (product: Product) => {
    const newQty = prompt(`الكمية الحالية: ${product.quantity}\nأدخل الكمية الجديدة:`, String(product.quantity))
    if (!newQty || isNaN(Number(newQty)) || Number(newQty) < 0) return

    try {
      await patchAmazonMutation.mutateAsync({
        sellerId: SELLER_ID,
        sku: product.sku,
        data: {
          product_type: product.product_type || 'HOME_ORGANIZERS_AND_STORAGE',
          patches: [
            {
              op: 'replace',
              path: '/attributes/quantity',
              value: [{ value: Number(newQty) }],
            },
          ],
        },
      })
      toast.success(`تم تحديث كمية ${product.sku} على Amazon`)
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل تحديث الكمية على Amazon')
    }
  }

  const products = data?.items ?? []

  const handleDelete = async (id: string) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا المنتج؟')) return
    try {
      await deleteMutation.mutateAsync(id)
      toast.success('تم حذف المنتج بنجاح')
    } catch {
      toast.error('فشل في حذف المنتج')
    }
  }

  const handleList = async (id: string) => {
    try {
      await listMutation.mutateAsync(id)
      toast.success('تم إرسال طلب الرفع للأمازون — جاري المعالجة...')

      // FIX: Poll for listing status and notify user of rejection
      const pollStatus = async () => {
        try {
          const res = await fetch('/api/v1/listings?status=failed')
          const data = await res.json()

          // Check if any listing for this product failed in the last 30 seconds
          const recentFailures = (data || []).filter((l: any) => {
            if (!l.completed_at || !l.error_message) return false
            const completedTime = new Date(l.completed_at).getTime()
            return Date.now() - completedTime < 30000 // last 30 seconds
          })

          if (recentFailures.length > 0) {
            const error = recentFailures[0].error_message
            toast.error(`❌ رفض أمازون: ${error}`, { duration: 15000 })
            refetch()
          }
        } catch (e) {
          console.warn('Polling error:', e)
        }
      }

      // Poll after 5 and 10 seconds
      setTimeout(pollStatus, 5000)
      setTimeout(pollStatus, 10000)
    } catch {
      toast.error('فشل في إرسال طلب الرفع')
    }
  }

  const handleEdit = (product: Product) => {
    navigate('/products/create', { state: { editMode: true, editProduct: product } })
  }

  const handleCompleteData = (product: Product) => {
    navigate('/products/create', { state: { editMode: true, editProduct: product, completeMode: true } })
  }

  const getMissingFields = (product: Product): string => {
    const missing: string[] = []

    // Check images
    if (!product.images || product.images.length === 0) missing.push('صور')

    // Check UPC/EAN
    if (!product.upc && !product.ean) missing.push('باركود')

    // Check bullet points
    if (!product.bullet_points || product.bullet_points.length === 0) missing.push('نقاط البيع')

    // Check brand
    if (!product.brand || product.brand === 'Generic') missing.push('براند')

    // Check product type
    if (!product.product_type) missing.push('نوع المنتج')

    return missing.join('، ')
  }

  // ==================== Excel Import ====================

  const handleDownloadTemplate = () => {
    const buffer = generateTemplateExcel()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'crazy_lister_template.xlsx'
    a.click()
    URL.revokeObjectURL(url)
    toast.success('تم تحميل القالب - املأه وارفعه')
  }

  const handleExcelFile = async (file: File) => {
    try {
      const buffer = await file.arrayBuffer()
      const result = importExcelFile(buffer)

      if (result.columnErrors.length > 0) {
        setValidationErrors(result.columnErrors)
        setExcelProducts([])
        setSelectedRows(new Set())
        setShowExcelModal(true)
        toast.error('الملف مش مطابق للقالب - حمّل القالب الأول')
        return
      }

      setExcelProducts(result.products)
      setSelectedRows(new Set(result.products.map((_, i) => i)))
      setValidationErrors(result.rowErrors.flatMap(re => re.errors))

      if (result.rowErrors.length > 0) {
        toast(`تم قراءة ${result.products.length} منتج - ${result.rowErrors.length} صف فيه أخطاء`, {
          icon: '⚠️',
        })
      } else {
        toast.success(`تم قراءة ${result.products.length} منتج بنجاح`)
      }

      setShowExcelModal(true)
    } catch (error: any) {
      toast.error(`فشل قراءة الملف: ${error.message}`)
    }
  }

  const toggleRow = (idx: number) => {
    setSelectedRows(prev => {
      const next = new Set(prev)
      next.has(idx) ? next.delete(idx) : next.add(idx)
      return next
    })
  }

  const toggleAll = () => {
    setSelectedRows(prev =>
      prev.size === excelProducts.length ? new Set() : new Set(excelProducts.map((_, i) => i))
    )
  }

  const handleImportSelected = async () => {
    if (selectedRows.size === 0) {
      toast.error('اختار منتج واحد على الأقل')
      return
    }

    setImporting(true)
    let success = 0
    let failed = 0
    const errors: string[] = []

    const selectedProducts = Array.from(selectedRows).map(i => excelProducts[i])

    for (let idx = 0; idx < selectedProducts.length; idx++) {
      const p = selectedProducts[idx]

      try {
        const payload: Record<string, unknown> = {
          sku: p.sku,
          seller_id: '',
          name: p.name,
          name_ar: p.name,
          name_en: p.name,
          brand: p.brand || 'Generic',
          price: p.price,
          quantity: p.quantity,
          description: p.description || '',
          product_type: p.category || 'HOME_ORGANIZERS_AND_STORAGE',
          condition: p.condition || 'New',
          fulfillment_channel: p.fulfillment_channel || 'MFN',
          country_of_origin: p.country_of_origin || 'CN',
          listing_copies: 1,
          bullet_points: p.bullet_points || [],
          images: [],  // Empty by default - will be incomplete
          attributes: {
            weight: p.weight,
            dimensions: p.dimensions,
            manufacturer: p.manufacturer,
            model_number: p.model_number,
          },
        }

        if (p.upc) payload.upc = p.upc
        if (p.ean) payload.ean = p.ean
        if (p.asin) payload.attributes = { ...payload.attributes, asin: p.asin }
        if (p.sale_price) payload.sale_price = p.sale_price
        if (p.sale_start_date) payload.sale_start_date = p.sale_start_date
        if (p.sale_end_date) payload.sale_end_date = p.sale_end_date
        if (p.handling_time) payload.handling_time = p.handling_time
        if (p.currency) payload.currency = p.currency
        if (p.parent_sku) payload.parent_sku = p.parent_sku
        if (p.variation_theme) payload.variation_theme = p.variation_theme
        if (p.is_parent) payload.is_parent = p.is_parent

        await productsApi.create(payload)
        success++
      } catch (error: any) {
        failed++
        const msg = error.response?.data?.detail || error.message || 'خطأ'
        errors.push(`صف ${p.row} (${p.name}): ${msg}`)
      }
    }

    setImporting(false)
    setShowExcelModal(false)
    setExcelProducts([])
    setSelectedRows(new Set())
    setValidationErrors([])

    if (success > 0) {
      toast.success(`✅ تم استيراد ${success} منتج${failed > 0 ? `، فشل ${failed}` : ''}`)
      if (failed > 0 && errors.length > 0) {
        toast.error(errors.slice(0, 3).join('\n'), { duration: 8000 })
      }
      refetch()
    } else {
      toast.error(`فشل استيراد كل المنتجات:\n${errors.slice(0, 5).join('\n')}`, { duration: 10000 })
    }
  }

  // ==================== Import from Amazon (SP-API) ====================
  const [amazonImporting, setAmazonImporting] = useState(false)
  const [fullSyncMode, setFullSyncMode] = useState(false)

  const handleImportFromAmazon = async (fullSync: boolean = false) => {
    const confirmMsg = fullSync
      ? 'سيتم استيراد المنتجات من Amazon مع كل التفاصيل (السعر، الكمية، الوصف، النقاط).\n\nهذا قد يستغرق بضع دقائق. هل تريد المتابعة؟'
      : 'سيتم استيراد آخر 10 منتجات من Amazon إلى قاعدة البيانات المحلية (بيانات أساسية فقط).\n\nهل تريد المتابعة؟'

    if (!window.confirm(confirmMsg)) return

    setAmazonImporting(true)
    setFullSyncMode(fullSync)
    try {
      const response = await fetch(`/api/v1/sp-api/import-products?limit=20&full_sync=${fullSync}`, {
        method: 'POST',
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'فشل الاستيراد')
      }

      const result = await response.json()

      if (result.success) {
        const syncLabel = fullSync ? 'مزامنة كاملة' : 'استيراد سريع'
        toast.success(`✅ ${result.message} (${result.full_details_fetched || 0} منتج بتفاصيل كاملة)`)
        refetch()
      } else {
        toast.error(result.message || 'فشل الاستيراد')
      }
    } catch (error: any) {
      toast.error(error.message || 'فشل الاتصال بـ Amazon')
    } finally {
      setAmazonImporting(false)
      setFullSyncMode(false)
    }
  }

  // ==================== Export Handlers ====================
  const handleExportToAmazon = async () => {
    try {
      // By default: فقط المنتجات الجديدة (بدون listings)
      const result = await exportMutation.mutateAsync(true)
      toast.success(result.message || 'تم رفع المنتجات الجديدة إلى Amazon بنجاح')
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل الرفع إلى Amazon')
    }
  }

  // إعادة رفع كل المنتجات (للحالات الخاصة)
  const handleReExportAllToAmazon = async () => {
    if (!window.confirm('⚠️ هل أنت متأكد؟ هتعمل إعادة رفع لكل المنتجات لـ Amazon (قد يسبب تكر listings)')) {
      return
    }
    try {
      const result = await exportMutation.mutateAsync(false)
      toast.success(result.message || 'تم إعادة رفع كل المنتجات إلى Amazon')
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل إعادة الرفع إلى Amazon')
    }
  }

  const handleExportPriceInventory = async () => {
    try {
      await exportPriceMutation.mutateAsync()
      toast.success('تم تصدير ملف Price & Inventory')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل التصدير')
    }
  }

  const handleExportListingLoader = async () => {
    try {
      await exportListingMutation.mutateAsync()
      toast.success('تم تصدير ملف Listing Loader')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل التصدير')
    }
  }

  // ==================== Loading / Error ====================
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

  // ==================== Render ====================
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{t('products.title')}</h1>
          <p className="text-text-secondary mt-1">{t('products.subtitle')} ({data?.total ?? 0})</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Export Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold px-4 py-3 rounded-lg transition-colors"
            >
              <FileDown className="w-5 h-5" />
              {t('products.exportExcel')}
              <ChevronDown className="w-4 h-4" />
            </button>
            {showExportMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowExportMenu(false)} />
                <div className="absolute right-0 mt-2 w-64 bg-bg-elevated border border-border-medium rounded-xl shadow-xl z-20 overflow-hidden">
                  <button
                    onClick={() => { handleExportPriceInventory(); setShowExportMenu(false) }}
                    disabled={exportPriceMutation.isPending}
                    className="w-full px-4 py-3 text-right text-sm text-white hover:bg-gray-700 transition flex items-center justify-between gap-2 disabled:opacity-50"
                  >
                    {exportPriceMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                    <span><span className="font-medium">{t('products.priceInventory')}</span><span className="text-text-muted text-xs block">{t('products.priceInventoryDesc')}</span></span>
                  </button>
                  <button
                    onClick={() => { handleExportListingLoader(); setShowExportMenu(false) }}
                    disabled={exportListingMutation.isPending}
                    className="w-full px-4 py-3 text-right text-sm text-white hover:bg-gray-700 transition flex items-center justify-between gap-2 border-t border-gray-700 disabled:opacity-50"
                  >
                    {exportListingMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                    <span><span className="font-medium">{t('products.listingLoader')}</span><span className="text-text-muted text-xs block">{t('products.listingLoaderDesc')}</span></span>
                  </button>
                </div>
              </>
            )}
          </div>

          <button
            onClick={handleExportToAmazon}
            disabled={exportMutation.isPending}
            className="flex items-center gap-2 bg-amazon-orange hover:bg-orange-600 text-white font-semibold px-6 py-3 rounded-xl transition-colors disabled:opacity-50"
            title="تصدير المنتجات الكاملة فقط (بدون منتجات ناقصة)"
          >
            {exportMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
            تصدير لـ Amazon
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleImportFromAmazon(false)}
              disabled={amazonImporting}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-3 rounded-xl transition-colors disabled:opacity-50 text-sm"
              title="استيراد سريع - بيانات أساسية فقط"
            >
              {amazonImporting && !fullSyncMode ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              استيراد سريع
            </button>
            <button
              onClick={() => handleImportFromAmazon(true)}
              disabled={amazonImporting}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-3 rounded-xl transition-colors disabled:opacity-50 text-sm"
              title="مزامنة كاملة - يجيب السعر والكمية والوصف وكل التفاصيل"
            >
              {amazonImporting && fullSyncMode ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              مزامنة كاملة
            </button>
          </div>

          {/* استيراد من Excel */}
          <label className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors cursor-pointer">
            <FileSpreadsheet className="w-5 h-5" />
            استيراد من Excel
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={e => { const f = e.target.files?.[0]; if (f) handleExcelFile(f); e.target.value = '' }}
              className="hidden"
            />
          </label>

          <Link
            to="/products/create"
            className="flex items-center gap-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold px-6 py-3 rounded-xl transition-colors"
          >
            <Plus className="w-5 h-5" />
            إضافة منتج
          </Link>
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={t('products.searchPlaceholder')}
            className="w-full pr-10 pl-4 py-3 border border-border-medium bg-bg-tertiary rounded-xl focus:ring-2 focus:ring-amazon-orange focus:border-amazon-orange text-text-primary placeholder-text-muted"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Filter className="w-5 h-5" /> تصفية
        </button>
      </div>

      {/* Products Table */}
      <div className="bg-bg-card rounded-xl border border-border-subtle overflow-hidden">
        <table className="neon-table">
          <thead className="bg-bg-elevated">
            <tr>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.image')}</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.product')}</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.sku')}</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.category')}</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.price')}</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.quantity')}</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.status')}</th>
              <th className="px-6 py-4 text-right text-sm font-semibold text-text-secondary">{t('products.columns.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product: Product) => {
              const isIncomplete = product.status === 'incomplete'

              // بناء URL الصورة
              let thumbUrl = ''
              if (product.images && product.images.length > 0) {
                const img = product.images[0]
                thumbUrl = img.startsWith('http') ? img :
                           img.startsWith('/api/') ? img :
                           `/api/v1/images/static/${img}`
              }

              return (
                <tr key={product.id} className={`${isIncomplete ? 'bg-neon-yellow/5' : ''}`}>
                  <td className="px-6 py-4">
                    {thumbUrl ? (
                      <img
                        src={thumbUrl}
                        alt={product.name}
                        className="w-10 h-10 rounded-lg object-cover border border-gray-700"
                        onError={(e) => {
                          // لو الصورة مكسورة، اعرض placeholder
                          (e.target as HTMLImageElement).style.display = 'none'
                          const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement
                          if (placeholder) placeholder.style.display = 'flex'
                        }}
                      />
                    ) : null}
                    <div
                      className="w-10 h-10 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center"
                      style={{ display: thumbUrl ? 'none' : 'flex' }}
                    >
                      <ImageIcon className="w-5 h-5 text-gray-600" />
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-white">{product.name}</p>
                      {isIncomplete && (
                        <span className="text-amber-500" title="ناقص بيانات Amazon">⚠️</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{product.brand}</p>
                    {isIncomplete && (
                      <p className="text-xs text-amber-500/70 mt-1">
                        ناقص: {getMissingFields(product)}
                      </p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400 font-mono">{product.sku}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{product.category}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-orange-500">{Number(product.price).toFixed(2)} ج.م</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{product.quantity}</td>
                  <td className="px-6 py-4"><StatusBadge status={product.status} /></td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {isIncomplete && (
                        <button
                          onClick={() => handleCompleteData(product)}
                          className="p-2 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 rounded-lg transition-colors"
                          title="إكمال البيانات"
                        >
                          <AlertCircle className="w-4 h-4" />
                        </button>
                      )}
                      <button onClick={() => handleEdit(product)} className="p-2 text-gray-400 hover:text-orange-500 hover:bg-orange-500/10 rounded-lg transition-colors" title="تعديل">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleList(product.id)}
                        disabled={listMutation.isPending}
                        className="p-2 text-gray-400 hover:text-green-500 hover:bg-green-500/10 rounded-lg transition-colors disabled:opacity-50"
                        title="رفع للأمازون"
                      >
                        {listMutation.isPending && listMutation.variables === product.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                      </button>
                      <button onClick={() => handleDelete(product.id)} disabled={deleteMutation.isPending} className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50" title="حذف">
                        {deleteMutation.isPending && deleteMutation.variables === product.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                      </button>

                      {/* SP-API Actions (Amazon Official) — shows when session OR .env credentials */}
                      <button
                        onClick={() => handleUpdatePriceOnAmazon(product)}
                        disabled={patchAmazonMutation.isPending}
                        className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-colors disabled:opacity-50"
                        title="تحديث السعر على Amazon (SP-API)"
                      >
                        {patchAmazonMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Cloud className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => handleDeleteFromAmazon(product.sku)}
                        disabled={deleteFromAmazonMutation.isPending}
                        className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                        title="حذف من Amazon (SP-API)"
                      >
                        {deleteFromAmazonMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <CloudOff className="w-4 h-4" />}
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {(!products || products.length === 0) && (
          <div className="text-center py-12 text-gray-500">
            <p>لا توجد منتجات</p>
            <Link to="/products/create" className="text-orange-500 font-medium hover:underline mt-2 inline-block">أضف أول منتج</Link>
          </div>
        )}
      </div>

      {/* ==================== Excel Import Modal ==================== */}
      {showExcelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[#1a1a2e] border border-gray-700 rounded-xl shadow-2xl w-full max-w-5xl max-h-[85vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-6 h-6 text-purple-400" />
                <div>
                  <h2 className="text-lg font-bold text-white">استيراد من Excel</h2>
                  <div className="flex items-center gap-3 text-xs text-gray-400 mt-1">
                    <span>{excelProducts.length} منتج صالح</span>
                    <span>•</span>
                    <span>{selectedRows.size} محدد</span>
                    <span>•</span>
                    <span>قالب عربي</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleDownloadTemplate}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
                  title="حمل القالب الرسمي"
                >
                  <Download className="w-4 h-4" /> تحميل القالب
                </button>
                <button onClick={() => { setShowExcelModal(false); setExcelProducts([]); setSelectedRows(new Set()); setValidationErrors([]) }} className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                  <X className="w-5 h-5 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Template Preview (before file is loaded) */}
            {excelProducts.length === 0 && (
              <div className="p-4 space-y-4">
                {/* Download Button - Prominent */}
                <button
                  onClick={handleDownloadTemplate}
                  className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-xl transition-all text-lg font-semibold shadow-lg shadow-blue-900/30"
                >
                  <Download className="w-6 h-6" />
                  تحميل القالب الرسمي (Excel)
                </button>

                {/* Template Preview Table */}
                <div className="p-3 bg-blue-900/20 border border-blue-800/50 rounded-lg">
                  <h3 className="text-sm font-medium text-blue-300 mb-2">📋 شكل القالب:</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-blue-900/30">
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50 bg-yellow-900/30">SKU ⚠️</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50 bg-yellow-900/30">اسم المنتج ⚠️</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50 bg-yellow-900/30">السعر ⚠️</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50 bg-yellow-900/30">الكمية ⚠️</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50">البراند</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50">الوصف</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50">الفئة</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50">الحالة</th>
                          <th className="px-2 py-1.5 text-right text-blue-300 border border-blue-800/50">الشحن</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="text-gray-400">
                          <td className="px-2 py-1.5 border border-gray-700/50 font-mono">SKU-001</td>
                          <td className="px-2 py-1.5 border border-gray-700/50">منظم ملابس داخلي 6 قطع</td>
                          <td className="px-2 py-1.5 border border-gray-700/50">199.99</td>
                          <td className="px-2 py-1.5 border border-gray-700/50">50</td>
                          <td className="px-2 py-1.5 border border-gray-700/50">Generic</td>
                          <td className="px-2 py-1.5 border border-gray-700/50 truncate max-w-[150px]">منظم ملابس داخلي...</td>
                          <td className="px-2 py-1.5 border border-gray-700/50">HOME_ORGANIZERS</td>
                          <td className="px-2 py-1.5 border border-gray-700/50">New</td>
                          <td className="px-2 py-1.5 border border-gray-700/50">MFN</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    <span className="text-yellow-500">⚠️ الأصفر</span> = أعمدة إجبارية (لازم تكون موجودة)
                    <span className="mx-2">|</span>
                    باقي الأعمدة اختيارية
                  </div>
                </div>
              </div>
            )}

            {/* Validation Errors */}
            {validationErrors.length > 0 && (
              <div className="p-4 bg-red-900/20 border-b border-red-800/50">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-300">أخطاء في الملف:</p>
                    <ul className="text-xs text-red-400 mt-1 space-y-0.5">
                      {validationErrors.map((err, i) => (
                        <li key={i}>• {err.message}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Toolbar */}
            <div className="flex items-center gap-2 p-4 border-b border-gray-700">
              <button
                onClick={toggleAll}
                className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-white transition-colors"
              >
                <Check className="w-4 h-4" />
                {selectedRows.size === excelProducts.length ? 'إلغاء الكل' : 'تحديد الكل'}
              </button>
              <button
                onClick={handleImportSelected}
                disabled={importing || selectedRows.size === 0}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              >
                {importing ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> جاري الاستيراد...</>
                ) : (
                  <><Upload className="w-4 h-4" /> استيراد {selectedRows.size} منتج</>
                )}
              </button>
            </div>

            {/* Product List */}
            <div className="flex-1 overflow-y-auto p-4">
              {excelProducts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>مفيش منتجات صالحة للاستيراد</p>
                  <p className="text-xs mt-1">حمّل القالب الرسمي واملاه بشكل صحيح</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {excelProducts.map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => toggleRow(idx)}
                      className={`w-full text-right p-3 rounded-lg border transition-colors ${
                        selectedRows.has(idx) ? 'border-purple-500 bg-purple-900/30' : 'border-gray-700 hover:bg-gray-800'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 ${
                          selectedRows.has(idx) ? 'border-purple-500 bg-purple-500' : 'border-gray-500'
                        }`}>
                          {selectedRows.has(idx) && <Check className="w-3 h-3 text-white" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-white truncate">{p.name}</p>
                          <p className="text-xs text-gray-400">
                            SKU: {p.sku} | السعر: {p.price} EGP | الكمية: {p.quantity}
                            {p.brand && ` | البراند: ${p.brand}`}
                          </p>
                        </div>
                        <span className="text-xs text-gray-500">صف {p.row}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
