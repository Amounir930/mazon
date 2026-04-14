import { useTranslation } from 'react-i18next'
import { Package, Upload, CheckCircle, XCircle, TrendingUp, Loader2, Plus, FileSpreadsheet, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useListings, useProducts } from '@/api/hooks'
import type { Listing } from '@/types/api'

export default function DashboardPage() {
  const { t } = useTranslation()
  const { data: productsData, isLoading: loadingProducts } = useProducts({ page_size: 1 })
  const { data: listings, isLoading: loadingListings } = useListings()

  const totalProducts = productsData?.total ?? 0
  const totalListings = listings?.length ?? 0
  const published = listings?.filter((l: Listing) => l.status === 'success').length ?? 0
  const queued = listings?.filter((l: Listing) => l.status === 'queued' || l.status === 'processing').length ?? 0
  const failed = listings?.filter((l: Listing) => l.status === 'failed').length ?? 0

  const isLoading = loadingProducts || loadingListings

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
      </div>
    )
  }

  const stats = [
    { label: t('dashboard.totalProducts'), value: totalProducts.toString(), icon: Package, accent: 'blue' as const },
    { label: t('dashboard.inQueue'), value: queued.toString(), icon: Upload, accent: 'orange' as const },
    { label: t('dashboard.published'), value: published.toString(), icon: CheckCircle, accent: 'green' as const },
    { label: t('dashboard.failed'), value: failed.toString(), icon: XCircle, accent: 'red' as const },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{t('dashboard.title')}</h1>
          <p className="text-text-secondary mt-1">{t('dashboard.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-neon-cyan/10 text-neon-cyan rounded-xl border border-neon-cyan/20">
          <TrendingUp className="w-5 h-5" />
          <span className="font-medium">{totalListings} {t('dashboard.totalListings')}</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map(({ label, value, icon: Icon, accent }) => {
          const iconColors: Record<string, string> = {
            blue: 'text-neon-blue',
            orange: 'text-amazon-orange',
            green: 'text-neon-cyan',
            red: 'text-neon-red',
          }
          return (
            <div key={label} className={`neon-card neon-card--accent neon-card--${accent} contain-layout`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-secondary">{label}</p>
                  <p className="text-3xl font-bold text-text-primary mt-1">{value}</p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-bg-elevated/50 border border-border-subtle flex items-center justify-center">
                  <Icon className={`w-6 h-6 ${iconColors[accent] || 'text-text-primary'}`} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <h2 className="text-lg font-semibold text-text-primary mt-8 mb-4">{t('dashboard.quickActions')}</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/products/create"
          className="neon-card neon-card--interactive group contain-layout"
        >
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amazon-orange/20 to-amazon-light/10 border border-amazon-orange/30 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
            <Plus className="w-6 h-6 text-amazon-orange" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">{t('dashboard.addNewProduct')}</h3>
          <p className="text-text-secondary text-sm">{t('dashboard.addNewProductDesc')}</p>
        </Link>

        <Link
          to="/products/create"
          className="neon-card neon-card--interactive group contain-layout"
        >
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-blue/20 to-neon-purple/10 border border-neon-blue/30 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
            <FileSpreadsheet className="w-6 h-6 text-neon-blue" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">{t('dashboard.bulkUpload')}</h3>
          <p className="text-text-secondary text-sm">{t('dashboard.bulkUploadDesc')}</p>
        </Link>

        <Link
          to="/listings"
          className="neon-card neon-card--interactive group contain-layout"
        >
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-blue/10 border border-neon-cyan/30 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
            <RefreshCw className="w-6 h-6 text-neon-cyan" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">{t('dashboard.viewQueue')}</h3>
          <p className="text-text-secondary text-sm">{t('dashboard.viewQueueDesc')}</p>
        </Link>
      </div>
    </div>
  )
}
