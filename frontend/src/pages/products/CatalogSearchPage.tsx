import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Search, Package, Loader2, ExternalLink, Plus, AlertCircle, Activity, Activity as Cloud } from 'lucide-react'
import { useSearchCatalogSPApi } from '@/api/hooks'
import { NeonButton, NeonCard } from '@/components/common'
import toast from 'react-hot-toast'

const searchTypes = ['KEYWORD', 'ASIN', 'UPC', 'EAN']

export default function CatalogSearchPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchType, setSearchType] = useState('KEYWORD')
  const [query, setQuery] = useState('')

  const [searchTriggered, setSearchTriggered] = useState(false)
  const [searchKeywords, setSearchKeywords] = useState<string | undefined>(undefined)
  const [searchIdentifiers, setSearchIdentifiers] = useState<string | undefined>(undefined)

  const { data: spApiData, isFetching: spApiFetching, refetch } = useSearchCatalogSPApi(
    searchTriggered
      ? { keywords: searchKeywords, identifiers: searchIdentifiers, page_size: 20 }
      : undefined
  )

  const isPending = spApiFetching

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) { toast.error(t('common.search') + '...'); return }

    if (searchType === 'KEYWORD') {
      setSearchKeywords(query.trim())
      setSearchIdentifiers(undefined)
    } else {
      setSearchKeywords(undefined)
      setSearchIdentifiers(query.trim())
    }

    setSearchTriggered(true)
    toast.success(t('catalogSearch.searchingVia'))
    setTimeout(() => refetch(), 100)
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

  const results = (spApiData?.items || []).map((item: any) => {
    const allImages: string[] = []
    if (item.images) {
      for (const imgGroup of item.images) {
        if (imgGroup.images) {
          for (const img of imgGroup.images) {
            if (img.variant === 'MAIN' && img.width === 500) allImages.push(img.link)
          }
        }
      }
    }
    let title = '', brand = ''
    if (item.summaries?.length > 0) {
      title = item.summaries[0].itemName || ''
      brand = item.summaries[0].brand || ''
    }
    return { title: title || item.itemName || '', asin: item.asin || '', brand, images: allImages }
  })

  const totalResults = spApiData?.total_results || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Activity className="w-6 h-6 text-neon-cyan" />
          {t('catalogSearch.title')}
        </h1>
        <p className="text-text-secondary mt-1">{t('catalogSearch.subtitle')}</p>
      </div>

      {/* Search Form */}
      <NeonCard>
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search Type Selector */}
          <div className="flex gap-2 flex-wrap">
            {searchTypes.map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setSearchType(type)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  searchType === type
                    ? 'bg-gradient-to-r from-amazon-orange to-amazon-light text-white shadow-lg'
                    : 'bg-bg-elevated text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                }`}
              >
                {t(`catalogSearch.searchTypes.${type.toLowerCase()}`)}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t(`catalogSearch.placeholders.${searchType.toLowerCase()}`)}
                className="neon-input pr-10"
              />
            </div>
            <NeonButton variant="success" type="submit" disabled={isPending}>
              {isPending ? (
                <><Loader2 className="w-5 h-5 animate-spin" /> {t('catalogSearch.searching')}</>
              ) : (
                <><Activity className="w-5 h-5" /> {t('catalogSearch.search')}</>
              )}
            </NeonButton>
          </div>
        </form>
      </NeonCard>

      {/* Error Message */}
      {spApiData && !spApiData.success && (
        <div className="neon-card neon-card--accent neon-card--red">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-neon-red mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-text-primary font-medium">{t('catalogSearch.searchFailed')}</p>
              <p className="text-text-secondary text-sm mt-1">{t('catalogSearch.searchFailedDesc')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {(results.length > 0 || isPending) && (
        <NeonCard>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-text-primary">
              {t('catalogSearch.results')} ({totalResults})
            </h2>
            <span className="text-xs text-neon-cyan flex items-center gap-1">
              <Activity className="w-3 h-3" />
              {t('catalogSearch.spApiOfficial')}
            </span>
          </div>

          {totalResults === 0 && !isPending ? (
            <div className="neon-empty">
              <div className="neon-empty__icon"><Package className="w-12 h-12" /></div>
              <h3 className="neon-empty__title">{t('catalogSearch.noResults')}</h3>
              <p className="neon-empty__description">{t('common.tryDifferentSearch')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((product: any, index: number) => (
                <div
                  key={index}
                  className="bg-bg-elevated/50 rounded-xl border border-border-subtle p-4 hover:border-amazon-orange/30 transition-colors"
                >
                  <div className="flex gap-4">
                    {/* Product Image */}
                    <div className="w-20 h-20 bg-bg-tertiary rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
                      {product.images?.[0] ? (
                        <img src={product.images[0]} alt={product.title} className="w-full h-full object-cover" />
                      ) : (
                        <Package className="w-8 h-8 text-text-muted" />
                      )}
                    </div>

                    {/* Product Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-text-primary font-medium truncate">{product.title || '-'}</h3>
                      <div className="flex flex-wrap gap-2 mt-2 text-xs text-text-secondary">
                        {product.asin && (
                          <span className="bg-bg-tertiary px-2 py-1 rounded-lg border border-border-subtle">
                            ASIN: {product.asin}
                          </span>
                        )}
                        {product.brand && (
                          <span className="bg-bg-tertiary px-2 py-1 rounded-lg border border-border-subtle">
                            {product.brand}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 flex-shrink-0">
                      <NeonButton variant="amazon" size="sm" onClick={() => handleAddProduct(product)}>
                        <Plus className="w-4 h-4" /> {t('common.add')}
                      </NeonButton>
                      {product.asin && (
                        <a
                          href={`https://www.amazon.eg/dp/${product.asin}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="neon-btn neon-btn--sm"
                        >
                          <ExternalLink className="w-4 h-4" /> {t('common.view')}
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </NeonCard>
      )}
    </div>
  )
}
