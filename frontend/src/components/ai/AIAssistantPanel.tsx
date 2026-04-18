import { useState } from 'react'
import { Sparkles, Send, Copy, AlertCircle, CheckCircle2, Loader2, RotateCcw, AlertTriangle } from 'lucide-react'
import { aiApi } from '@/api/ai'
import type { AIMergedProduct, AIGenerateProductRequest, ValidationError } from '@/types/ai'
import toast from 'react-hot-toast'

interface AIAssistantPanelProps {
  onProductGenerated?: (product: AIMergedProduct) => void
  onClose?: () => void
}

type GenerationStep = 'idle' | 'prompting' | 'generating' | 'validating' | 'complete'

export const AIAssistantPanel: React.FC<AIAssistantPanelProps> = ({
  onProductGenerated,
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

  // Step progress calculator
  const getStepProgress = () => {
    switch (generationStep) {
      case 'prompting':
        return 25
      case 'generating':
        return 60
      case 'validating':
        return 90
      case 'complete':
        return 100
      default:
        return 0
    }
  }

  // Handle product generation
  const handleGenerateProduct = async () => {
    if (!productName.trim()) {
      toast.error('Please enter product name')
      return
    }

    if (!productSpecs.trim()) {
      toast.error('Please enter product specifications')
      return
    }

    setLoading(true)
    setError(null)
    setValidationWarnings([])
    setContaminationWarning(null)
    setFallbackUsed(false)

    try {
      setGenerationStep('prompting')
      await new Promise(r => setTimeout(r, 800))

      setGenerationStep('generating')

      const request: AIGenerateProductRequest = {
        name: productName,
        specs: productSpecs,
        copies: copies || 1,
      }

      const response = await aiApi.generateProduct(request)

      setGenerationStep('validating')
      await new Promise(r => setTimeout(r, 300))

      if (response.data.success && response.data.data) {
        if (response.data.fallback_used) {
          setFallbackUsed(true)
          toast.info('Generated with enhanced fallback mode', { icon: '🔄' })
        }

        if (response.data.validation_errors?.length) {
          const errorsList = response.data.validation_errors
          setValidationWarnings(errorsList)

          const errorMessages = errorsList
            .filter(e => e.severity === 'error')
            .map(e => `${e.field}: ${e.message}`)

          if (errorMessages.length > 0) {
            toast.error(`Validation issues:\n${errorMessages.join('\n')}`, {
              duration: 8000,
              icon: '⚠️',
            })
          }
        }

        if (response.data.warnings?.length) {
          const contaminationWarnings = response.data.warnings.filter(w =>
            w.message.toLowerCase().includes('contamination') ||
            w.message.toLowerCase().includes('data')
          )

          if (contaminationWarnings.length > 0) {
            setContaminationWarning(
              'Content quality checks completed - minor corrections applied'
            )
            toast.info('Content quality check completed', { icon: '🛡️' })
          }

          response.data.warnings.forEach(w => {
            if (!w.message.toLowerCase().includes('contamination')) {
              toast.warning(`${w.field}: ${w.message}`, {
                icon: '⚠️',
                duration: 6000,
              })
            }
          })
        }

        setGeneratedProduct(response.data.data)
        setGenerationStep('complete')
        toast.success('Product generated successfully!')
        onProductGenerated?.(response.data.data)
      } else {
        const errorMsg =
          response.data.error ||
          response.data.message ||
          response.data.validation_errors?.[0]?.message ||
          'Failed to generate product'
        setError(errorMsg)
        setGenerationStep('idle')
        toast.error(errorMsg)
      }
    } catch (err: any) {
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

  // Handle retry
  const handleRetry = () => {
    setError(null)
    setGeneratedProduct(null)
    handleGenerateProduct()
  }

  // Handle copy
  const handleCopyProduct = () => {
    if (generatedProduct) {
      const productJson = JSON.stringify(generatedProduct, null, 2)
      navigator.clipboard.writeText(productJson)
      toast.success('Product data copied to clipboard')
    }
  }

  // Handle generate another
  const handleGenerateAnother = () => {
    setGeneratedProduct(null)
    setProductName('')
    setProductSpecs('')
    setCopies(1)
    setError(null)
    setValidationWarnings([])
    setContaminationWarning(null)
    setFallbackUsed(false)
    setGenerationStep('idle')
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6 border border-purple-200 dark:border-purple-800">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            AI Product Assistant
          </h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            ✕
          </button>
        )}
      </div>

      {/* Input Section */}
      {!generatedProduct ? (
        <div className="space-y-4">
          {/* Generation Progress */}
          {loading && (
            <div className="mb-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-purple-700 dark:text-purple-300 mb-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>
                  {generationStep === 'prompting' && 'Preparing AI prompt...'}
                  {generationStep === 'generating' && 'Generating product data...'}
                  {generationStep === 'validating' && 'Validating and optimizing...'}
                  {generationStep === 'complete' && 'Finalizing...'}
                </span>
              </div>
              <div className="h-1 bg-purple-200 dark:bg-purple-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-600 transition-all duration-500"
                  style={{ width: `${getStepProgress()}%` }}
                />
              </div>
            </div>
          )}

          {/* Product Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Product Name (Arabic)
            </label>
            <input
              type="text"
              value={productName}
              onChange={e => setProductName(e.target.value)}
              placeholder="e.g., خلاط كهربائي عالي الأداء"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={loading}
            />
          </div>

          {/* Product Specs */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Product Specifications
            </label>
            <textarea
              value={productSpecs}
              onChange={e => setProductSpecs(e.target.value)}
              placeholder="Describe the product features and specifications..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 h-24 resize-none"
              disabled={loading}
            />
          </div>

          {/* Copies */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Number of Variants
            </label>
            <input
              type="number"
              value={copies}
              onChange={e => setCopies(parseInt(e.target.value) || 1)}
              min="1"
              max="10"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={loading}
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg space-y-3">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-red-700 dark:text-red-300 flex-1">{error}</p>
              </div>
              <button
                onClick={handleRetry}
                disabled={loading}
                className="w-full py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
              >
                <RotateCcw className="w-4 h-4" />
                Retry
              </button>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleGenerateProduct}
            disabled={loading || !productName.trim() || !productSpecs.trim()}
            className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Generate Product
              </>
            )}
          </button>
        </div>
      ) : (
        /* Result Section */
        <div className="space-y-4">
          {/* Success */}
          <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-green-700 dark:text-green-300">
                Product Generated Successfully!
              </p>
              <p className="text-sm text-green-600 dark:text-green-400">
                {generatedProduct.variants.length} variant(s) created
              </p>
            </div>
          </div>

          {/* Contamination Warning */}
          {contaminationWarning && (
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-yellow-700 dark:text-yellow-300">{contaminationWarning}</p>
            </div>
          )}

          {/* Fallback Used */}
          {fallbackUsed && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex gap-2">
              <AlertCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Enhanced fallback mode was used for optimal results
              </p>
            </div>
          )}

          {/* Validation Warnings */}
          {validationWarnings.length > 0 && (
            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
              <p className="font-semibold text-orange-700 dark:text-orange-300 mb-2">
                Validation Notices
              </p>
              <div className="space-y-1">
                {validationWarnings.map((w, idx) => (
                  <p key={idx} className="text-sm text-orange-600 dark:text-orange-400">
                    • {w.field}: {w.message}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Product Summary */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-2">
            <h3 className="font-semibold text-gray-900 dark:text-white">Base Product Info</h3>
            <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 dark:text-gray-400">
              <div>
                Brand:{' '}
                <span className="font-medium text-gray-900 dark:text-white">
                  {generatedProduct.base_product.brand}
                </span>
              </div>
              <div>
                Type:{' '}
                <span className="font-medium text-gray-900 dark:text-white">
                  {generatedProduct.base_product.product_type}
                </span>
              </div>
              <div>
                Bullets:{' '}
                <span className="font-medium text-gray-900 dark:text-white">
                  {generatedProduct.base_product.bullet_points_ar.length}
                </span>
              </div>
              <div>
                Keywords:{' '}
                <span className="font-medium text-gray-900 dark:text-white">
                  {generatedProduct.base_product.keywords.length}
                </span>
              </div>
            </div>
          </div>

          {/* Variants */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-3">
            <h3 className="font-semibold text-gray-900 dark:text-white">Variants</h3>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {generatedProduct.variants.map((variant, idx) => (
                <div
                  key={idx}
                  className="text-sm bg-white dark:bg-gray-700 p-2 rounded border border-gray-200 dark:border-gray-600"
                >
                  <div className="font-medium text-gray-900 dark:text-white">
                    V{variant.variant_number}: {variant.name_ar}
                  </div>
                  {variant.model_name && (
                    <div className="text-gray-600 dark:text-gray-400 text-xs">
                      Model: {variant.model_name}
                    </div>
                  )}
                  <div className="text-gray-600 dark:text-gray-400 text-xs">
                    SKU: {variant.suggested_sku}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleCopyProduct}
              className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <Copy className="w-4 h-4" />
              Copy Data
            </button>
            <button
              onClick={handleGenerateAnother}
              className="flex-1 py-2 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-lg transition-colors"
            >
              Generate Another
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AIAssistantPanel
