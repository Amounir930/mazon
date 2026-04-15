import { useTranslation } from 'react-i18next'
import { Loader2, Play, RotateCcw, AlertCircle, CheckCircle, Info, Image as ImageIcon } from 'lucide-react'
import { useListings, useRetryListing } from '@/api/hooks'
import { StatusBadge, NeonButton } from '@/components/common'
import type { Listing } from '@/types/api'
import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'

export default function ListingQueuePage() {
  const { t } = useTranslation()
  const { data: listings, isLoading } = useListings({})
  const retryMutation = useRetryListing()
  
  // Track failed listings to show notifications
  const [notifiedFailed, setNotifiedFailed] = useState<Set<string>>(new Set())
  const prevListingsRef = useRef<Listing[] | null>(null)

  // Detect new failures and show notifications
  useEffect(() => {
    if (!listings || listings.length === 0) return

    const prevListings = prevListingsRef.current
    const currentListings = listings as Listing[]

    if (prevListings) {
      // Check for listings that just became failed
      for (const listing of currentListings) {
        const prevListing = prevListings.find((l: Listing) => l.id === listing.id)
        const wasNotFailed = prevListing && prevListing.status !== 'failed'
        const isNowFailed = listing.status === 'failed'
        const notNotified = !notifiedFailed.has(listing.id)

        if (wasNotFailed && isNowFailed && notNotified) {
          // Show error notification with details
          const errorMsg = listing.error_message || 'سبب غير معروف'
          toast.error(
            <div className="space-y-2">
              <div className="font-semibold flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                تم رفض المنتج
              </div>
              <div className="text-sm opacity-90">{errorMsg}</div>
              <div className="text-xs opacity-70">SKU: {listing.product_id?.slice(0, 20) || listing.id?.slice(0, 8)}</div>
            </div>,
            { duration: 10000, id: `failed-${listing.id}` }
          )
          setNotifiedFailed(prev => new Set(prev).add(listing.id))
        }

        // Also notify for newly successful listings
        const wasNotSuccess = prevListing && prevListing.status !== 'success'
        const isNowSuccess = listing.status === 'success'
        if (wasNotSuccess && isNowSuccess) {
          toast.success(
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              <span>تم قبول المنتج على Amazon! {listing.amazon_asin ? `— ASIN: ${listing.amazon_asin}` : ''}</span>
            </div>,
            { duration: 5000, id: `success-${listing.id}` }
          )
        }
      }
    }

    prevListingsRef.current = currentListings
  }, [listings, notifiedFailed])

  const handleRetry = async (listingId: string) => {
    try {
      await retryMutation.mutateAsync(listingId)
      toast.success('تمت إعادة المحاولة!')
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'فشل إعادة المحاولة')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
      </div>
    )
  }

  const allListings = (listings as Listing[]) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{t('listingQueue.title')}</h1>
          <p className="text-text-secondary mt-1">{t('listingQueue.subtitle')} ({allListings.length})</p>
        </div>
        <div className="flex gap-3">
          <NeonButton variant="amazon" size="sm">
            <Play className="w-4 h-4" />
            {t('listingQueue.listAll')}
          </NeonButton>
          <NeonButton variant="info" size="sm" styleType="outline"
            onClick={() => window.location.reload()}>
            <RotateCcw className="w-4 h-4" />
            {t('listingQueue.refresh')}
          </NeonButton>
        </div>
      </div>

      {/* Failed Listings Alert Banner */}
      {allListings.filter(l => l.status === 'failed').length > 0 && (
        <div className="bg-neon-red/5 border border-neon-red/20 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-neon-red flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-neon-red mb-1">
              ⚠️ فيه {allListings.filter(l => l.status === 'failed').length} منتج تم رفضه من Amazon
            </h3>
            <p className="text-xs text-text-secondary">
              حوّل الماوس على شارة "فشل" عشان تشوف سبب الرفض. تقدر تضغط "إعادة محاولة" بعد ما تصلح المشكلة.
            </p>
          </div>
        </div>
      )}

      {/* Success Info Banner */}
      {allListings.filter(l => l.status === 'success').length > 0 && (
        <div className="bg-neon-cyan/5 border border-neon-cyan/20 rounded-xl p-4 flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-neon-cyan flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-neon-cyan mb-1">
              ✅ {allListings.filter(l => l.status === 'success').length} منتج تم قبوله على Amazon
            </h3>
            <p className="text-xs text-text-secondary">
              المنتجات دي نازلة على Amazon بنجاح.
            </p>
          </div>
        </div>
      )}

      {/* Stats - Top position */}
      {allListings.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-bg-card rounded-2xl border border-border-subtle p-5 flex items-center justify-between">
            <div className="text-left">
              <p className="text-xs text-text-muted mb-1">{t('listingQueue.stats.success')}</p>
              <p className="text-3xl font-bold text-text-primary">
                {allListings.filter(l => l.status === 'success').length}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-bg-elevated border border-border-subtle flex items-center justify-center">
              <span className="w-3 h-3 rounded-full bg-neon-cyan"></span>
            </div>
          </div>

          <div className="bg-bg-card rounded-2xl border border-border-subtle p-5 flex items-center justify-between">
            <div className="text-left">
              <p className="text-xs text-text-muted mb-1">{t('listingQueue.stats.queued')}</p>
              <p className="text-3xl font-bold text-text-primary">
                {allListings.filter(l => l.status === 'queued').length}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-bg-elevated border border-border-subtle flex items-center justify-center">
              <span className="w-3 h-3 rounded-full bg-neon-yellow"></span>
            </div>
          </div>

          <div className="bg-bg-card rounded-2xl border border-border-subtle p-5 flex items-center justify-between">
            <div className="text-left">
              <p className="text-xs text-text-muted mb-1">{t('listingQueue.stats.processing')}</p>
              <p className="text-3xl font-bold text-text-primary">
                {allListings.filter(l => l.status === 'processing' || l.status === 'submitted').length}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-bg-elevated border border-border-subtle flex items-center justify-center">
              <span className="w-3 h-3 rounded-full bg-neon-blue"></span>
            </div>
          </div>

          <div className="bg-bg-card rounded-2xl border border-border-subtle p-5 flex items-center justify-between">
            <div className="text-left">
              <p className="text-xs text-text-muted mb-1">{t('listingQueue.stats.failed')}</p>
              <p className="text-3xl font-bold text-text-primary">
                {allListings.filter(l => l.status === 'failed').length}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-bg-elevated border border-border-subtle flex items-center justify-center">
              <span className="w-3 h-3 rounded-full bg-neon-red"></span>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="neon-card p-0 overflow-hidden">
        <table className="neon-table">
          <thead>
            <tr>
              <th className="text-right">{t('listingQueue.columns.number')}</th>
              <th className="text-left">{t('listingQueue.columns.product')}</th>
              <th className="text-right">{t('listingQueue.columns.status')}</th>
              <th className="text-right">{t('listingQueue.columns.error')}</th>
              <th className="text-right">{t('listingQueue.columns.feedId')}</th>
              <th className="text-right">{t('listingQueue.columns.time')}</th>
              <th className="text-right">{t('listingQueue.columns.action')}</th>
            </tr>
          </thead>
          <tbody>
            {allListings.map((listing: Listing, idx: number) => {
              // Build thumbnail URL
              const images = (listing as any).product_images || []
              const thumbUrl = images.length > 0
                ? images[0].startsWith('http')
                  ? images[0]
                  : images[0].startsWith('/api/')
                    ? images[0]
                    : `/api/v1/images/static/${images[0]}`
                : ''

              return (
              <tr key={listing.id} className={listing.status === 'failed' ? 'bg-neon-red/5' : ''}>
                <td className="text-text-secondary text-sm text-right">{idx + 1}</td>
                <td className="text-left">
                  <div className="flex items-center gap-3">
                    {/* Product Image */}
                    {thumbUrl ? (
                      <img
                        src={thumbUrl}
                        alt={(listing as any).product_name || ''}
                        className="w-10 h-10 rounded-lg object-cover border border-border-subtle flex-shrink-0"
                        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-bg-elevated border border-border-subtle flex items-center justify-center flex-shrink-0">
                        <ImageIcon className="w-5 h-5 text-text-muted" />
                      </div>
                    )}
                    {/* Product Name */}
                    <div className="min-w-0">
                      <div className="font-medium text-text-primary text-sm truncate" title={(listing as any).product_name || ''}>
                        {(listing as any).product_name || listing.product_id?.slice(0, 20) || '...'}
                      </div>
                      {listing.amazon_asin && (
                        <div className="text-xs text-text-muted font-mono">ASIN: {listing.amazon_asin}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="text-right">
                  <StatusBadge status={listing.status} error={listing.error_message} />
                </td>
                <td className="text-right max-w-xs">
                  {listing.error_message ? (
                    <div className="text-xs text-neon-red" title={listing.error_message}>
                      {listing.error_message.slice(0, 50)}...
                    </div>
                  ) : (
                    <span className="text-xs text-text-muted">-</span>
                  )}
                </td>
                <td className="font-mono text-text-secondary text-sm text-right">
                  {listing.feed_submission_id || listing.sp_api_submission_id || '-'}
                </td>
                <td className="text-text-secondary text-sm text-right">
                  {listing.created_at ? new Date(listing.created_at).toLocaleTimeString('ar-EG') : '-'}
                </td>
                <td className="text-right">
                  {listing.status === 'failed' && (
                    <button
                      className="neon-btn neon-btn--warning neon-btn--sm"
                      onClick={() => handleRetry(listing.id!)}
                      disabled={retryMutation.isPending}
                    >
                      <RotateCcw className="w-4 h-4" />
                      إعادة محاولة
                    </button>
                  )}
                  {listing.status === 'success' && (
                    <span className="text-xs text-neon-cyan flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      تم
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!listings || listings.length === 0) && (
          <div className="neon-empty">
            <div className="neon-empty__icon">
              <Info className="w-12 h-12" />
            </div>
            <h3 className="neon-empty__title">{t('listingQueue.emptyTitle')}</h3>
            <p className="neon-empty__description">{t('listingQueue.emptyDesc')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
