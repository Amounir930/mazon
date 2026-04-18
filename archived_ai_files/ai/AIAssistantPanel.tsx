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
    <div className="neon-card neon-card--accent neon-card--blue p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-amazon-orange/10 border border-amazon-orange/20">
          <Sparkles className="w-6 h-6 text-amazon-orange" />
        </div>
        <div>
          <h3 className="font-bold text-xl text-text-primary">مساعد الذكاء الاصطناعي الذكي</h3>
          <p className="text-sm text-text-secondary">املأ البيانات الأساسية ودع الـ AI يتولى التفاصيل المعقدة</p>
        </div>
      </div>

      {/* Learned Fields Warning */}
      {learnedFields.length > 0 && (
        <div className="mb-6 p-4 rounded-xl bg-neon-red/5 border border-neon-red/20 shadow-inner">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-neon-red mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="font-bold text-text-primary mb-2">تنبيه: حقول مرفوضة سابقاً من Amazon</p>
              <div className="flex flex-wrap gap-2">
                {learnedFields.map((field, i) => (
                  <span key={i} className="px-2 py-1 bg-neon-red/10 text-neon-red rounded-lg text-xs font-bold border border-neon-red/10">
                    {field}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Form */}
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Product Name */}
          <div className="space-y-2">
            <label className="text-sm font-bold text-text-primary flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amazon-orange"></span>
              اسم المنتج
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="مثال: خلاط كهربائي 300 واط"
              dir="rtl"
              className="neon-input neon-input--blue w-full h-12"
            />
          </div>

          {/* Number of Variants */}
          <div className="space-y-2">
            <label className="text-sm font-bold text-text-primary flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amazon-orange"></span>
              عدد العروض / النسخ
            </label>
            <div className="flex items-center gap-3 h-12">
              <button
                type="button"
                onClick={() => {
                  const v = Math.max(1, copies - 1)
                  setCopies(v)
                  onCopiesChange?.(v)
                }}
                disabled={copies <= 1}
                className="w-12 h-full flex items-center justify-center rounded-xl border border-border-medium bg-bg-elevated hover:bg-bg-hover disabled:opacity-30 transition-all active:scale-95"
              >
                <Minus className="w-5 h-5 text-text-secondary" />
              </button>
              <div className="flex-1 h-full flex items-center justify-center bg-bg-card border border-border-subtle rounded-xl font-bold text-xl text-amazon-orange">
                {copies}
              </div>
              <button
                type="button"
                onClick={() => {
                  const v = Math.min(10, copies + 1)
                  setCopies(v)
                  onCopiesChange?.(v)
                }}
                disabled={copies >= 10}
                className="w-12 h-full flex items-center justify-center rounded-xl border border-border-medium bg-bg-elevated hover:bg-bg-hover disabled:opacity-30 transition-all active:scale-95"
              >
                <Plus className="w-5 h-5 text-text-secondary" />
              </button>
            </div>
          </div>
        </div>

        {/* Specifications */}
        <div className="space-y-2">
          <label className="text-sm font-bold text-text-primary flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-amazon-orange"></span>
            المواصفات الأساسية (اكتب كل سطر ميزة)
          </label>
          <textarea
            value={specs}
            onChange={e => setSpecs(e.target.value)}
            placeholder={"محرك قوي\nشفرات ستانلس\nضمان عامين"}
            dir="rtl"
            rows={4}
            className="neon-input neon-textarea w-full p-4"
          />
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={loading || !name.trim() || !specs.trim()}
          className="neon-btn neon-btn--primary w-full h-14 text-lg font-black shadow-lg shadow-amazon-orange/20 active:scale-[0.98] transition-all disabled:opacity-40"
        >
          {loading ? (
            <div className="flex items-center justify-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin" />
              <span>جاري تحليل البيانات وتوليد المنتج...</span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-3">
              <Sparkles className="w-6 h-6" />
              <span>توليد {copies > 1 ? `${copies} منتجات مختلفة` : 'المنتج'} بالذكاء الاصطناعي</span>
            </div>
          )}
        </button>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mt-6 space-y-3">
          {warnings.map((warning, i) => (
            <div key={i} className="flex items-center gap-3 text-sm text-amazon-orange bg-amazon-orange/5 rounded-xl p-4 border border-amazon-orange/20">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span className="font-medium">{warning}</span>
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
    amazon_product_type: base.amazon_product_type,
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
