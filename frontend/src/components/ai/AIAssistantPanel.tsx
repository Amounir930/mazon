/**
 * AI Assistant Panel — Product Creation
 * Dark Theme + Neon Style
 */
import { useState, memo, useCallback, useEffect } from 'react'
import { Sparkles, Loader2, AlertTriangle, HelpCircle, Plus, Minus } from 'lucide-react'
import { toast } from 'react-hot-toast'
import { aiApi } from '@/api/ai'
import type { BaseProductData, ProductVariant, AIMergedProduct } from '@/types/ai'

interface AIAssistantPanelProps {
  onProductsGenerated: (products: AIMergedProduct[]) => void
  onCopiesChange?: (copies: number) => void
  productId?: string
}

export const AIAssistantPanel = memo(function AIAssistantPanel({ onProductsGenerated, onCopiesChange, productId }: AIAssistantPanelProps) {
  const [name, setName] = useState('')
  const [specs, setSpecs] = useState('')
  const [copies, setCopies] = useState(1)
  const [loading, setLoading] = useState(false)
  const [warnings, setWarnings] = useState<string[]>([])
  const [learnedFields, setLearnedFields] = useState<string[]>([])
  const [learnedLoading, setLearnedLoading] = useState(false)

  useEffect(() => {
    if (!productId) return
    setLearnedLoading(true)
    fetch(`/api/v1/ai/learned-fields/${productId}`)
      .then(r => r.json())
      .then(data => setLearnedFields(data.learned_fields || []))
      .catch(() => {})
      .finally(() => setLearnedLoading(false))
  }, [productId])

  const handleGenerate = useCallback(async () => {
    if (!name.trim()) { toast.error('أدخل اسم المنتج'); return }
    if (!specs.trim()) { toast.error('أدخل المواصفات'); return }

    setLoading(true)
    setWarnings([])

    try {
      const result = await aiApi.generateProduct({ name: name.trim(), specs: specs.trim(), copies })
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
    <div className="neon-card neon-card--accent neon-card--pink">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple/20 to-neon-pink/10 border border-neon-purple/30">
          <Sparkles className="w-5 h-5 text-neon-purple" />
        </div>
        <div>
          <h3 className="font-bold text-lg text-text-primary">مساعد الذكاء الاصطناعي</h3>
          <p className="text-sm text-text-secondary">اكتب اسم المنتج والمواصفات — AI هيعبّي كل شيء</p>
        </div>
      </div>

      {/* Learned Fields Warning */}
      {learnedFields.length > 0 && (
        <div className="mb-4 p-3 rounded-lg bg-neon-red/5 border border-neon-red/20">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-neon-red mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-text-primary mb-1">حقول سبق رفضها Amazon:</p>
              <div className="flex flex-wrap gap-1">
                {learnedFields.map((field, i) => (
                  <span key={i} className="px-2 py-0.5 bg-neon-red/10 text-neon-red rounded text-xs font-medium">
                    {field}
                  </span>
                ))}
              </div>
              <p className="text-xs text-text-secondary mt-1">AI سيتضمن هذه الحقول تلقائياً</p>
            </div>
          </div>
        </div>
      )}

      {/* How it works */}
      <div className="mb-6 p-4 rounded-lg bg-bg-elevated/50 border border-border-subtle">
        <div className="flex items-start gap-2">
          <HelpCircle className="w-5 h-5 text-neon-purple mt-0.5 flex-shrink-0" />
          <div className="text-sm text-text-secondary">
            <p className="font-medium text-text-primary mb-1">إزاي يشتغل؟</p>
            <ol className="list-decimal list-inside space-y-1 text-text-muted">
              <li>اكتب <strong className="text-text-secondary">اسم المنتج</strong></li>
              <li>اكتب <strong className="text-text-secondary">المواصفات</strong></li>
              <li>اضبط <strong className="text-text-secondary">العدد</strong></li>
              <li>اضغط <strong className="text-text-secondary">توليد</strong></li>
            </ol>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="space-y-4">
        {/* Product Name */}
        <div className="neon-input-group">
          <label className="neon-label neon-label--required">اسم المنتج</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="مثال: خلاط كهربائي 5 سرعات 300 واط"
            dir="rtl"
            className="neon-input neon-input--pink"
          />
        </div>

        {/* Specifications */}
        <div className="neon-input-group">
          <label className="neon-label neon-label--required">المواصفات</label>
          <textarea
            value={specs}
            onChange={e => setSpecs(e.target.value)}
            placeholder={"5 سرعات\nستانلس ستيل\nسهل التنظيف"}
            dir="rtl"
            rows={3}
            className="neon-input neon-textarea resize-none"
          />
          <span className="neon-helper">اكتب كل المواصفات — كل ما كانت أكتر، النتيجة أدق</span>
        </div>

        {/* Number of Variants */}
        <div className="neon-input-group">
          <label className="neon-label">عدد العروض</label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                const v = Math.max(1, copies - 1)
                setCopies(v)
                onCopiesChange?.(v)
              }}
              disabled={copies <= 1}
              className="w-10 h-10 flex items-center justify-center rounded-xl border border-border-medium bg-bg-elevated hover:bg-bg-hover disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <Minus className="w-4 h-4 text-text-secondary" />
            </button>
            <input
              type="number"
              min="1"
              max="10"
              value={copies}
              onChange={e => {
                const v = parseInt(e.target.value)
                if (!isNaN(v) && v >= 1 && v <= 10) {
                  setCopies(v)
                  onCopiesChange?.(v)
                }
              }}
              className="neon-input w-20 text-center text-lg font-bold"
            />
            <button
              type="button"
              onClick={() => {
                const v = Math.min(10, copies + 1)
                setCopies(v)
                onCopiesChange?.(v)
              }}
              disabled={copies >= 10}
              className="w-10 h-10 flex items-center justify-center rounded-xl border border-border-medium bg-bg-elevated hover:bg-bg-hover disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <Plus className="w-4 h-4 text-text-secondary" />
            </button>
            <span className="text-sm text-text-muted">{copies === 1 ? 'منتج' : 'منتجات'}</span>
          </div>
          <span className="neon-helper">كل عرض اسم + وصف + SKU مختلف</span>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={loading || !name.trim() || !specs.trim()}
          className="neon-btn neon-btn--rainbow w-full h-12 text-base font-bold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> جاري التوليد...</>
          ) : (
            <><Sparkles className="w-5 h-5" /> توليد منتج{copies > 1 ? ` (${copies})` : ''} بالذكاء الاصطناعي</>
          )}
        </button>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mt-4 space-y-2">
          {warnings.map((warning, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-neon-yellow bg-neon-yellow/5 rounded-lg p-3 border border-neon-yellow/20">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
})

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
    included_components: base.included_components || '',
    name_ar: variant.name_ar,
    name_en: variant.name_en,
    description_ar: variant.description_ar,
    description_en: variant.description_en,
    suggested_sku: variant.suggested_sku,
    ai_generated: true,
  }
}
