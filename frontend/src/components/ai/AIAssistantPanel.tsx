import { useState } from 'react'
import { Activity as Sparkles, Send, Copy, AlertCircle, CheckCircle, Loader2, RefreshCw as RotateCcw, AlertTriangle, X, Search as Tag } from 'lucide-react'
import { aiApi } from '@/api/ai'
import type { AIMergedProduct, AIGenerateProductRequest, ValidationError } from '@/types/ai'
import toast from 'react-hot-toast'

interface AIAssistantPanelProps {
  onProductsGenerated?: (products: any[]) => void
  onCopiesChange?: (count: number) => void
  onPageChange?: (page: number) => void
  onClose?: () => void
}

type GenerationStep = 'idle' | 'prompting' | 'generating' | 'validating' | 'complete'

export const AIAssistantPanel: React.FC<AIAssistantPanelProps> = ({
  onProductsGenerated,
  onCopiesChange,
  onPageChange,
  onClose,
}) => {
  const [productName, setProductName] = useState('')
  const [productSpecs, setProductSpecs] = useState('')
  const [copies, setCopies] = useState(1)
  const [loading, setLoading] = useState(false)
  const [generatedProduct, setGeneratedProduct] = useState<AIMergedProduct | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [generationStep, setGenerationStep] = useState<GenerationStep>('idle')
  const [contaminationWarning, setContaminationWarning] = useState<string | null>(null)
  const [validationWarnings, setValidationWarnings] = useState<ValidationError[]>([])
  const [fallbackUsed, setFallbackUsed] = useState(false)

  const handleCopiesChange = (val: number) => {
    const newCount = Math.min(10, Math.max(1, val))
    setCopies(newCount)
    onCopiesChange?.(newCount)
  }

  const getStepProgress = () => {
    switch (generationStep) {
      case 'prompting': return 25
      case 'generating': return 60
      case 'validating': return 90
      case 'complete': return 100
      default: return 0
    }
  }

  const handleGenerateProduct = async () => {
    if (!productName.trim() || !productSpecs.trim()) {
      toast.error('يرجى إدخال اسم المنتج والمواصفات')
      return
    }

    setLoading(true)
    setError(null)
    setValidationWarnings([])
    setContaminationWarning(null)
    setFallbackUsed(false)

    try {
      setGenerationStep('prompting')
      await new Promise(r => setTimeout(r, 500))

      setGenerationStep('generating')
      const request: AIGenerateProductRequest = {
        name: productName,
        specs: productSpecs,
        copies: copies,
      }

      const response = await aiApi.generateProduct(request)

      setGenerationStep('validating')
      await new Promise(r => setTimeout(r, 300))

      if (response.data.success && response.data.data) {
        const result = response.data.data
        
        if (response.data.fallback_used) setFallbackUsed(true)
        if (response.data.validation_errors) setValidationWarnings(response.data.validation_errors)
        
        setGeneratedProduct(result)
        setGenerationStep('complete')
        toast.success('✅ تم توليد بيانات المنتج بنجاح!')
        
        // Flatten data for the parent (merge base with each variant)
        const flattened = result.variants.map(v => ({
          ...result.base_product,
          ...v,
          model_name: v.model_name || result.base_product.model_name || '',
          metadata: result.metadata
        }))
        
        onProductsGenerated?.(flattened)
      } else {
        throw new Error(response.data.error || response.data.message || 'Failed to generate product')
      }
    } catch (err: any) {
      console.error('❌ AI Generation Error:', err)
      const errorMsg =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        err?.message ||
        'An error occurred while generating product'
      setError(errorMsg)
      setGenerationStep('idle')
      toast.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    setError(null)
    handleGenerateProduct()
  }

  const handleReset = () => {
    setGeneratedProduct(null)
    setGenerationStep('idle')
    setError(null)
    setProductName('')
    setProductSpecs('')
    setCopies(1)
  }

  return (
    <div className="neon-card neon-card--accent neon-card--blue p-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amazon-orange/10 rounded-xl border border-amazon-orange/20">
            <Sparkles className="w-6 h-6 text-amazon-orange animate-pulse" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-text-primary">AI Product Assistant</h2>
            <p className="text-sm text-text-muted">مساعدك الذكي لإنشاء قوائم المنتجات باحترافية</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5 text-text-muted" />
          </button>
        )}
      </div>

      {!generatedProduct ? (
        <div className="space-y-5">
          {loading && (
            <div className="mb-4 p-4 bg-neon-blue/10 rounded-xl border border-neon-blue/20 shadow-[0_0_15px_rgba(0,242,255,0.05)]">
              <div className="flex items-center gap-3 text-sm text-neon-blue mb-3">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="font-bold tracking-wide uppercase text-[10px]">
                  {generationStep === 'prompting' && 'Preparing Brain...'}
                  {generationStep === 'generating' && 'Thinking & Creating...'}
                  {generationStep === 'validating' && 'Perfecting Data...'}
                  {generationStep === 'complete' && 'Ready!'}
                </span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-neon-blue shadow-[0_0_12px_rgba(0,242,255,0.6)] transition-all duration-700 ease-out"
                  style={{ width: `${getStepProgress()}%` }}
                />
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-black text-text-secondary uppercase tracking-widest">
              Product Name (Arabic)
            </label>
            <input
              type="text"
              value={productName}
              onChange={e => setProductName(e.target.value)}
              placeholder="مثال: خلاط كهربائي عالي الأداء 500 واط"
              className="neon-input w-full text-lg"
              disabled={loading}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-black text-text-secondary uppercase tracking-widest">
              Product Specifications
            </label>
            <textarea
              value={productSpecs}
              onChange={e => setProductSpecs(e.target.value)}
              placeholder="اكتب مواصفات المنتج، مميزاته، أو أي تفاصيل تقنية..."
              className="neon-input neon-textarea w-full h-28 resize-none"
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-black text-text-secondary uppercase tracking-widest">
              Number of Variants (1-10)
            </label>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 bg-bg-elevated p-1 rounded-xl border border-border-subtle shadow-inner">
                <button
                  onClick={() => handleCopiesChange(copies - 1)}
                  disabled={loading || copies <= 1}
                  className="p-2.5 hover:bg-white/5 disabled:opacity-20 rounded-lg text-text-primary transition-all active:scale-95"
                >
                  <RotateCcw className="w-4 h-4 -rotate-90" />
                </button>
                <span className="text-xl font-black w-12 text-center text-text-primary">{copies}</span>
                <button
                  onClick={() => handleCopiesChange(copies + 1)}
                  disabled={loading || copies >= 10}
                  className="p-2.5 hover:bg-white/5 disabled:opacity-20 rounded-lg text-text-primary transition-all active:scale-95"
                >
                  <RotateCcw className="w-4 h-4 rotate-90" />
                </button>
              </div>
              <div className="flex-1 p-3 bg-white/5 rounded-xl border border-white/5">
                <p className="text-[10px] text-text-muted leading-relaxed uppercase font-bold tracking-tighter">
                  سيقوم الذكاء الاصطناعي بتوليد {copies} نسخ مختلفة بأسماء وSKU فريدة لزيادة فرص ظهورك.
                </p>
              </div>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-neon-red/10 border border-neon-red/20 rounded-xl space-y-3 animate-in fade-in zoom-in-95">
              <div className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-neon-red flex-shrink-0" />
                <p className="text-sm text-text-primary leading-relaxed">{error}</p>
              </div>
              <button
                onClick={handleRetry}
                disabled={loading}
                className="w-full py-2.5 bg-neon-red hover:bg-red-600 disabled:opacity-50 text-white font-black rounded-xl transition-all flex items-center justify-center gap-2 text-xs shadow-lg shadow-neon-red/20"
              >
                <RotateCcw className="w-4 h-4" />
                إعادة المحاولة
              </button>
            </div>
          )}

          <button
            onClick={handleGenerateProduct}
            disabled={loading || !productName.trim() || !productSpecs.trim()}
            className="w-full py-4 bg-gradient-to-r from-amazon-orange to-amazon-light hover:translate-y-[-2px] active:translate-y-[0] disabled:opacity-50 disabled:translate-y-0 text-white font-black rounded-xl transition-all flex items-center justify-center gap-3 text-lg shadow-xl shadow-amazon-orange/30 group"
          >
            {loading ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="tracking-widest uppercase">Generating Magic...</span>
              </>
            ) : (
              <>
                <Send className="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                <span>توليد البيانات الآن</span>
              </>
            )}
          </button>
        </div>
      ) : (
        <div className="space-y-6 animate-in zoom-in-95 duration-500">
          <div className="p-5 bg-amazon-orange/10 border border-amazon-orange/20 rounded-2xl flex items-center justify-between shadow-lg shadow-amazon-orange/5">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-amazon-orange/20 rounded-xl shadow-inner">
                <CheckCircle className="w-6 h-6 text-amazon-orange" />
              </div>
              <div>
                <p className="text-lg font-black text-text-primary">تم التوليد بنجاح!</p>
                <p className="text-xs text-text-muted font-bold uppercase tracking-wider">
                  تم تجهيز {generatedProduct.variants.length} نسخة احترافية
                </p>
              </div>
            </div>
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 text-xs font-black text-amazon-orange hover:bg-amazon-orange/10 rounded-xl border border-amazon-orange/20 transition-all active:scale-95"
            >
              <RotateCcw className="w-4 h-4" />
              توليد جديد
            </button>
          </div>

          <div className="bg-bg-elevated border border-border-subtle rounded-2xl overflow-hidden shadow-2xl">
            <div className="p-3 bg-white/5 border-b border-border-subtle flex items-center justify-between px-5">
              <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">نظرة عامة على البيانات</span>
              <span className="text-[9px] font-black bg-neon-blue/20 text-neon-blue px-3 py-1 rounded-full border border-neon-blue/30 uppercase tracking-tighter">
                {generatedProduct.metadata?.model_used || 'GPT-4 Engine'}
              </span>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-1.5">
                  <p className="text-[10px] text-text-muted uppercase font-black tracking-widest">Brand</p>
                  <p className="text-sm text-text-primary font-bold bg-white/5 p-2 rounded-lg border border-white/5">{generatedProduct.base_product.brand}</p>
                </div>
                <div className="space-y-1.5">
                  <p className="text-[10px] text-text-muted uppercase font-black tracking-widest">Model Number</p>
                  <p className="text-sm text-text-primary font-mono font-bold bg-white/5 p-2 rounded-lg border border-white/5">{generatedProduct.base_product.model_number}</p>
                </div>
              </div>
              <div className="space-y-1.5">
                <p className="text-[10px] text-text-muted uppercase font-black tracking-widest">Example Name (En)</p>
                <p className="text-sm text-text-primary leading-relaxed font-medium bg-white/5 p-3 rounded-lg border border-white/5 italic">
                  {generatedProduct.variants[0].name_en}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-neon-cyan/5 border border-neon-cyan/20 p-5 rounded-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 bg-neon-cyan/5 rounded-full -mr-4 -mt-4 blur-3xl group-hover:bg-neon-cyan/10 transition-all" />
            <div className="flex gap-4 relative z-10">
              <Sparkles className="w-6 h-6 text-neon-cyan flex-shrink-0 animate-pulse" />
              <div className="space-y-3">
                <p className="text-sm font-black text-text-primary">البيانات جاهزة للمراجعة</p>
                <p className="text-xs text-text-muted leading-relaxed font-medium">
                  تم ملء الحقول الإجبارية والوصف والكلمات المفتاحية تلقائياً. يمكنك الآن الانتقال للخطوة التالية لمراجعة الأسعار والصور.
                </p>
                <button
                  onClick={() => onPageChange?.(1)}
                  className="mt-2 px-4 py-2 bg-neon-cyan/20 hover:bg-neon-cyan/30 text-neon-cyan text-xs font-bold rounded-lg border border-neon-cyan/30 transition-all flex items-center gap-2"
                >
                  <Tag className="w-3.5 h-3.5" />
                  View Mandatory Fields
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 pt-5 border-t border-border-subtle flex items-center justify-between opacity-50">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]" />
          <span className="text-[9px] font-black text-text-muted uppercase tracking-[0.2em]">Engine Stable</span>
        </div>
        <p className="text-[9px] text-text-muted font-bold tracking-wider">
          PLATFORM <span className="text-neon-cyan">V3.0.4</span> — POWERED BY <span className="text-amazon-orange">CEREBRAS</span>
        </p>
      </div>
    </div>
  )
}

export default AIAssistantPanel
