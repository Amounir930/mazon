import { useTranslation } from 'react-i18next'
import { Loader2, Play, RotateCcw } from 'lucide-react'
import { useListings } from '@/api/hooks'
import { StatusBadge, NeonButton } from '@/components/common'
import type { Listing } from '@/types/api'

export default function ListingQueuePage() {
  const { t } = useTranslation()
  const { data: listings, isLoading } = useListings({})

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{t('listingQueue.title')}</h1>
          <p className="text-text-secondary mt-1">{t('listingQueue.subtitle')} ({listings?.length ?? 0})</p>
        </div>
        <div className="flex gap-3">
          <NeonButton variant="amazon" size="sm">
            <Play className="w-4 h-4" />
            {t('listingQueue.listAll')}
          </NeonButton>
          <NeonButton variant="info" size="sm" styleType="outline">
            <RotateCcw className="w-4 h-4" />
            {t('listingQueue.refresh')}
          </NeonButton>
        </div>
      </div>

      {/* Table */}
      <div className="neon-card p-0 overflow-hidden">
        <table className="neon-table">
          <thead>
            <tr>
              <th>{t('listingQueue.columns.number')}</th>
              <th>{t('listingQueue.columns.product')}</th>
              <th>{t('listingQueue.columns.status')}</th>
              <th>{t('listingQueue.columns.feedId')}</th>
              <th>{t('listingQueue.columns.time')}</th>
              <th>{t('listingQueue.columns.action')}</th>
            </tr>
          </thead>
          <tbody>
            {listings?.map((listing: Listing, idx: number) => (
              <tr key={listing.id}>
                <td className="text-text-secondary">{idx + 1}</td>
                <td className="font-medium text-text-primary">
                  {listing.product_id?.slice(0, 8)}...
                </td>
                <td>
                  <StatusBadge status={listing.status} />
                </td>
                <td className="font-mono text-text-secondary text-sm">
                  {listing.feed_submission_id || '-'}
                </td>
                <td className="text-text-secondary text-sm">
                  {listing.created_at ? new Date(listing.created_at).toLocaleTimeString() : '-'}
                </td>
                <td>
                  {listing.status === 'failed' && (
                    <button className="neon-btn neon-btn--warning neon-btn--sm">
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!listings || listings.length === 0) && (
          <div className="neon-empty">
            <div className="neon-empty__icon">
              <RotateCcw className="w-12 h-12" />
            </div>
            <h3 className="neon-empty__title">{t('listingQueue.emptyTitle')}</h3>
            <p className="neon-empty__description">{t('listingQueue.emptyDesc')}</p>
          </div>
        )}
      </div>

      {/* Stats - Redesigned like the image */}
      {listings && listings.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Order: نجح → في الطابور → قيد المعالجة → فشل (RTL) */}
          <div className="bg-bg-card rounded-2xl border border-border-subtle p-5 flex items-center justify-between">
            <div className="text-left">
              <p className="text-xs text-text-muted mb-1">{t('listingQueue.stats.success')}</p>
              <p className="text-3xl font-bold text-text-primary">
                {listings.filter((l: Listing) => l.status === 'success').length}
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
                {listings.filter((l: Listing) => l.status === 'queued').length}
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
                {listings.filter((l: Listing) => l.status === 'processing' || l.status === 'submitted').length}
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
                {listings.filter((l: Listing) => l.status === 'failed').length}
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-bg-elevated border border-border-subtle flex items-center justify-center">
              <span className="w-3 h-3 rounded-full bg-neon-red"></span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
