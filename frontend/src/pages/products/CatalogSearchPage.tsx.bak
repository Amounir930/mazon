import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Package, Loader2, ExternalLink, Plus, AlertCircle, Cloud } from 'lucide-react'
import { useSearchCatalogSPApi } from '@/api/hooks'
import toast from 'react-hot-toast'

const searchTypes = [
  { id: 'KEYWORD', label: 'كلمة مفتاحية', placeholder: 'مثال: iPhone 15, سماعات بلوتوث' },
  { id: 'ASIN', label: 'ASIN', placeholder: 'مثال: B08XYZ1234' },
  { id: 'UPC', label: 'UPC', placeholder: 'مثال: 012345678901' },
  { id: 'EAN', label: 'EAN', placeholder: 'مثال: 5901234123457' },
]

export default function CatalogSearchPage() {
  const navigate = useNavigate()
  const [searchType, setSearchType] = useState('KEYWORD')
  const [query, setQuery] = useState('')

  // SP-API catalog search (uses .env credentials from backend)
  const [searchTriggered, setSearchTriggered] = useState(false)
  const [searchKeywords, setSearchKeywords] = useState<string | undefined>(undefined)
  const [searchIdentifiers, setSearchIdentifiers] = useState<string | undefined>(undefined)

  const { data: spApiData, isFetching: spApiFetching, refetch } = useSearchCatalogSPApi(
    searchTriggered
      ? {
          keywords: searchKeywords,
          identifiers: searchIdentifiers,
          page_size: 20,
        }
      : undefined
  )

  const isPending = spApiFetching

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) {
      toast.error('يرجى إدخال كلمة بحث')
      return
    }

    if (searchType === 'KEYWORD') {
      setSearchKeywords(query.trim())
      setSearchIdentifiers(undefined)
    } else {
      setSearchKeywords(undefined)
      setSearchIdentifiers(query.trim())
    }

    setSearchTriggered(true)
    toast.success('جاري البحث عبر SP-API الرسمي...')

    // Trigger refetch with new params
    setTimeout(() => {
      refetch()
    }, 100)
  }

  const handleAddProduct = (product: any) => {
    navigate('/products/create', {
      state: {
        editMode: false,
        editProduct: {
          sku: product.sku || product.asin || '',
          name: product.title || product.name || '',
          name_ar: product.title || product.name || '',
          name_en: product.title || product.name || '',
          price: product.price || 0,
          quantity: product.quantity || 0,
          brand: product.brand || '',
          description: product.description || '',
          images: product.images || [],
          category: product.category || '',
          asin: product.asin || '',
          upc: product.upc || '',
          ean: product.ean || '',
        },
      },
    })
  }

  const currentSearchType = searchTypes.find((t) => t.id === searchType)

  // Normalize SP-API results
  const results = (spApiData?.items || []).map((item: any) => {
    // Extract images
    const allImages: string[] = []
    if (item.images) {
      for (const imgGroup of item.images) {
        if (imgGroup.images) {
          for (const img of imgGroup.images) {
            if (img.variant === 'MAIN' && img.width === 500) {
              allImages.push(img.link)
            }
          }
        }
      }
    }

    // Extract title from summaries
    let title = ''
    let brand = ''
    if (item.summaries && item.summaries.length > 0) {
      title = item.summaries[0].itemName || ''
      brand = item.summaries[0].brand || ''
    }

    return {
      title: title || item.itemName || 'بدون اسم',
      asin: item.asin || '',
      brand,
      images: allImages,
      price: null,
    }
  })

  const totalResults = spApiData?.total_results || 0

  return (
    <div className="space-y-6" dir="rtl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Cloud className="w-6 h-6 text-green-500" />
          البحث في كتالوج Amazon (SP-API)
        </h1>
        <p className="text-gray-400 mt-1">ابحث في كتالوج Amazon الرسمي وأضف المنتجات لمتجرك</p>
      </div>

      {/* Search Form */}
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 shadow-2xl">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search Type Selector */}
          <div className="flex gap-2 flex-wrap">
            {searchTypes.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => setSearchType(id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  searchType === id
                    ? 'bg-amazon-orange text-white'
                    : 'bg-[#1a1a2e] text-gray-400 hover:text-white hover:bg-[#2a2a3e]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={currentSearchType?.placeholder}
                className="w-full pr-10 pl-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={isPending}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  جاري البحث...
                </>
              ) : (
                <>
                  <Cloud className="w-5 h-5" />
                  بحث
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error Message */}
      {spApiData && !spApiData.success && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
          <div>
            <p className="text-red-400 font-medium">فشل البحث</p>
            <p className="text-red-300/70 text-sm mt-1">فشل البحث عبر SP-API — تحقق من الـ credentials</p>
          </div>
        </div>
      )}

      {/* Results */}
      {(results.length > 0 || isPending) && (
        <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">
              نتائج البحث ({totalResults} نتيجة)
            </h2>
            <span className="text-xs text-green-400 flex items-center gap-1">
              <Cloud className="w-3 h-3" />
              SP-API الرسمي
            </span>
          </div>

          {totalResults === 0 && !isPending ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">لم يتم العثور على نتائج</p>
              <p className="text-gray-500 text-sm mt-1">جرّب كلمة بحث مختلفة</p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((product: any, index: number) => (
                <div
                  key={index}
                  className="bg-[#1a1a2e] rounded-lg border border-gray-700/50 p-4 hover:border-amazon-orange/50 transition-colors"
                >
                  <div className="flex gap-4">
                    {/* Product Image */}
                    <div className="w-20 h-20 bg-[#0a0a0f] rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
                      {product.images?.[0] ? (
                        <img
                          src={product.images[0]}
                          alt={product.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Package className="w-8 h-8 text-gray-600" />
                      )}
                    </div>

                    {/* Product Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-medium truncate">
                        {product.title || 'بدون اسم'}
                      </h3>
                      <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-400">
                        {product.asin && (
                          <span className="bg-[#0a0a0f] px-2 py-1 rounded">
                            ASIN: {product.asin}
                          </span>
                        )}
                        {product.brand && (
                          <span className="bg-[#0a0a0f] px-2 py-1 rounded">
                            {product.brand}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 flex-shrink-0">
                      <button
                        onClick={() => handleAddProduct(product)}
                        className="flex items-center gap-1 px-3 py-2 bg-amazon-orange hover:bg-orange-600 text-white rounded-lg text-sm font-medium transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                        إضافة
                      </button>
                      {product.asin && (
                        <a
                          href={`https://www.amazon.eg/dp/${product.asin}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 px-3 py-2 bg-[#0a0a0f] hover:bg-[#1a1a2e] text-gray-400 rounded-lg text-sm transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                          عرض
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
