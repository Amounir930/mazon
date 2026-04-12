import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Package, Loader2, ExternalLink, Plus, AlertCircle } from 'lucide-react'
import { useCatalogSearch } from '@/api/hooks'
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
  const { mutate: search, data, isPending, error, reset } = useCatalogSearch()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) {
      toast.error('يرجى إدخال كلمة بحث')
      return
    }
    // Reset error state before new search
    reset()
    search({ query: query.trim(), searchType })
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

  return (
    <div className="space-y-6" dir="rtl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Search className="w-6 h-6 text-amazon-orange" />
          البحث في كتالوج Amazon
        </h1>
        <p className="text-gray-400 mt-1">ابحث عن منتجات موجودة في Amazon وأضفها لمتجرك</p>
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
              className="px-6 py-3 bg-amazon-orange hover:bg-orange-600 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  جاري البحث...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  بحث
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Debug Info */}
      {process.env.NODE_ENV === 'development' && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-3 text-xs text-yellow-400 font-mono">
          Debug: data={data ? 'yes' : 'no'} | error={error ? 'yes' : 'no'} | isPending={isPending ? 'yes' : 'no'}
          {data && <pre className="mt-2 overflow-auto">{JSON.stringify(data, null, 2)}</pre>}
          {error && <pre className="mt-2 overflow-auto">{JSON.stringify(error, null, 2)}</pre>}
        </div>
      )}

      {/* Error Message */}
      {error && !data && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
          <div>
            <p className="text-red-400 font-medium">فشل البحث</p>
            <p className="text-red-300/70 text-sm mt-1">
              {(error as any)?.response?.data?.detail || (error as any)?.message || 'حدث خطأ أثناء البحث'}
            </p>
            {process.env.NODE_ENV === 'development' && (
              <pre className="mt-2 text-xs text-red-300/50 overflow-auto max-h-32">
                {JSON.stringify(error, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      {data && (
        <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">
              نتائج البحث ({data.total} نتيجة)
            </h2>
            <span className="text-xs text-gray-500">
              البحث: {data.query} ({data.search_type})
            </span>
          </div>

          {data.total === 0 ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">لم يتم العثور على نتائج</p>
              <p className="text-gray-500 text-sm mt-1">جرّب كلمة بحث مختلفة أو نوع بحث آخر</p>
            </div>
          ) : (
            <div className="space-y-3">
              {(data.results || []).map((product: any, index: number) => (
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
                          alt={product.title || product.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Package className="w-8 h-8 text-gray-600" />
                      )}
                    </div>

                    {/* Product Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-medium truncate">
                        {product.title || product.name || 'بدون اسم'}
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
                        {product.price && (
                          <span className="text-amazon-orange font-semibold">
                            ${product.price}
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
