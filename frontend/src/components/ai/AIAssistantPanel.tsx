/**
 * AI Assistant Panel — Product Creation
 * 
 * Optimized: React.memo + useCallback to prevent unnecessary re-renders.
 * Base + Delta Pattern: generates N variants in single API call.
 */
import { useState, memo, useCallback, useEffect } from 'react'
import { Sparkles, Loader2, AlertTriangle, HelpCircle, Plus, Minus } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { aiApi } from '@/api/ai'
import type { BaseProductData, ProductVariant, AIMergedProduct } from '@/types/ai'

interface AIAssistantPanelProps {
  onProductsGenerated: (products: AIMergedProduct[]) => void
  productId?: string  // For fetching learned fields
}

export const AIAssistantPanel = memo(function AIAssistantPanel({ onProductsGenerated, productId }: AIAssistantPanelProps) {
  const [name, setName] = useState('')
  const [specs, setSpecs] = useState('')
  const [copies, setCopies] = useState(1)
  const [loading, setLoading] = useState(false)
  const [warnings, setWarnings] = useState<string[]>([])
  const [learnedFields, setLearnedFields] = useState<string[]>([])
  const [learnedLoading, setLearnedLoading] = useState(false)

  // Fetch learned fields when productId is provided
  useEffect(() => {
    if (!productId) return
    setLearnedLoading(true)
    fetch(`/api/v1/ai/learned-fields/${productId}`)
      .then(r => r.json())
      .then(data => {
        setLearnedFields(data.learned_fields || [])
      })
      .catch(() => {})
      .finally(() => setLearnedLoading(false))
  }, [productId])

  const handleGenerate = useCallback(async () => {
    if (!name.trim()) { toast.error('أدخل اسم المنتج'); return }
    if (!specs.trim()) { toast.error('أدخل المواصفات'); return }

    setLoading(true)
    setWarnings([])

    try {
      const result = await aiApi.generateProduct({
        name: name.trim(),
        specs: specs.trim(),
        copies,
      })

      const mergedProducts: AIMergedProduct[] = result.variants.map(
        (variant: ProductVariant) => mergeProduct(result.base_product, variant)
      )

      setWarnings(result.warnings || [])
      onProductsGenerated(mergedProducts)
      toast.success(`تم توليد ${result.count} ${result.count === 1 ? 'منتج' : 'منتجات'}!`)
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || 'فشل التوليد'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }, [name, specs, copies, onProductsGenerated])

  return (
    <div className="rounded-xl border-2 border-violet-200 dark:border-violet-800 bg-gradient-to-br from-violet-50 via-white to-purple-50 dark:from-violet-950/40 dark:via-gray-900 dark:to-purple-950/40 p-6 shadow-lg">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-violet-600">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-bold text-lg text-violet-900 dark:text-violet-100">مساعد الذكاء الاصطناعي</h3>
          <p className="text-sm text-violet-600 dark:text-violet-400">اكتب اسم المنتج والمواصفات — AI هيعبّي كل شيء</p>
        </div>
      </div>

      {/* Learned Fields Warning */}
      {learnedFields.length > 0 && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-red-900 dark:text-red-100 mb-1">⚠️ حقول سبق رفضها Amazon:</p>
              <div className="flex flex-wrap gap-1">
                {learnedFields.map((field, i) => (
                  <span key={i} className="px-2 py-0.5 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 rounded text-xs font-medium">
                    {field}
                  </span>
                ))}
              </div>
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">AI سيتضمن هذه الحقول تلقائياً</p>
            </div>
          </div>
        </div>
      )}

      {/* How it works */}
      <div className="mb-6 p-4 rounded-lg bg-white/70 dark:bg-gray-800/70 border border-violet-100 dark:border-violet-900">
        <div className="flex items-start gap-2">
          <HelpCircle className="w-5 h-5 text-violet-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-gray-600 dark:text-gray-300">
            <p className="font-medium text-gray-900 dark:text-white mb-1">إزاي يشتغل؟</p>
            <ol className="list-decimal list-inside space-y-1 text-gray-500 dark:text-gray-400">
              <li>اكتب <strong>اسم المنتج</strong></li>
              <li>اكتب <strong>المواصفات</strong></li>
              <li>اضبط <strong>العدد</strong></li>
              <li>اضغط <strong>توليد</strong></li>
            </ol>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="space-y-4">
        {/* Product Name */}
        <div>
          <label className="text-sm font-semibold mb-1 block text-gray-700 dark:text-gray-200">
            📦 اسم المنتج <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="مثال: خلاط كهربائي 5 سرعات 300 واط"
            dir="rtl"
            className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-violet-500 text-base"
          />
        </div>

        {/* Specifications */}
        <div>
          <label className="text-sm font-semibold mb-1 block text-gray-700 dark:text-gray-200">
            📋 المواصفات <span className="text-red-500">*</span>
          </label>
          <textarea
            value={specs}
            onChange={e => setSpecs(e.target.value)}
            placeholder={"5 سرعات\nستانلس ستيل\nسهل التنظيف"}
            dir="rtl"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-violet-500 text-base resize-none"
          />
          <p className="text-xs text-gray-400 mt-1">اكتب كل المواصفات — كل ما كانت أكتر، النتيجة أدق</p>
        </div>

        {/* Number of Variants — Number Input with +/- */}
        <div>
          <label className="text-sm font-semibold mb-1 block text-gray-700 dark:text-gray-200">
            🔢 عدد العروض
          </label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setCopies(Math.max(1, copies - 1))}
              disabled={copies <= 1}
              className="w-10 h-10 flex items-center justify-center rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <Minus className="w-4 h-4" />
            </button>
            <input
              type="number"
              min="1"
              max="10"
              value={copies}
              onChange={e => {
                const v = parseInt(e.target.value)
                if (!isNaN(v) && v >= 1 && v <= 10) setCopies(v)
              }}
              className="w-20 text-center px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-lg font-bold focus:ring-2 focus:ring-violet-500"
            />
            <button
              type="button"
              onClick={() => setCopies(Math.min(10, copies + 1))}
              disabled={copies >= 10}
              className="w-10 h-10 flex items-center justify-center rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <Plus className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-400">{copies === 1 ? 'منتج' : 'منتجات'}</span>
          </div>
          <p className="text-xs text-gray-400 mt-1">كل عرض اسم + وصف + SKU مختلف</p>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={loading || !name.trim() || !specs.trim()}
          className="w-full h-12 text-base font-bold bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed rounded-lg flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              جاري التوليد...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              توليد منتج{copies > 1 ? ` (${copies})` : ''} بالذكاء الاصطناعي
            </>
          )}
        </button>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mt-4 space-y-2">
          {warnings.map((warning, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-amber-700 bg-amber-50 dark:bg-amber-950/30 rounded-lg p-3 border border-amber-200">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
})

/** Merge base_product + variant into a single product */
function mergeProduct(base: BaseProductData, variant: ProductVariant): AIMergedProduct {
  return {
    brand: base.brand,
    manufacturer: base.manufacturer,
    product_type: base.product_type,
    price: base.price,
    ean: base.ean,
    upc: base.upc,
    bullet_points_ar: base.bullet_points_ar,
    bullet_points_en: base.bullet_points_en,
    keywords: base.keywords,
    material: base.material,
    target_audience: base.target_audience,
    condition: base.condition,
    fulfillment_channel: base.fulfillment_channel,
    country_of_origin: base.country_of_origin,
    model_number: base.model_number,
    name_ar: variant.name_ar,
    name_en: variant.name_en,
    description_ar: variant.description_ar,
    description_en: variant.description_en,
    suggested_sku: variant.suggested_sku,
    ai_generated: true,
  }
}
