import { useTranslation } from 'react-i18next'
import { Download, FileText, BarChart3 } from 'lucide-react'
import { NeonCard } from '@/components/common'

export default function ReportsPage() {
  const { t } = useTranslation()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">{t('reports.title')}</h1>
        <p className="text-text-secondary mt-1">{t('reports.subtitle')}</p>
      </div>

      {/* Report Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <NeonCard accent="orange" interactive className="group">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amazon-orange/20 to-amazon-light/10 border border-amazon-orange/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
              <FileText className="w-6 h-6 text-amazon-orange" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-text-primary mb-1">{t('reports.excelReport')}</h3>
              <p className="text-sm text-text-secondary">{t('reports.excelReportDesc')}</p>
              <button className="neon-btn neon-btn--amazon neon-btn--sm mt-3">
                <Download className="w-4 h-4" /> {t('reports.export')}
              </button>
            </div>
          </div>
        </NeonCard>

        <NeonCard accent="blue" interactive className="group">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-blue/20 to-neon-purple/10 border border-neon-blue/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
              <BarChart3 className="w-6 h-6 text-neon-blue" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-text-primary mb-1">{t('reports.statsReport')}</h3>
              <p className="text-sm text-text-secondary">{t('reports.statsReportDesc')}</p>
              <button className="neon-btn neon-btn--primary neon-btn--sm mt-3">
                {t('reports.viewReport')}
              </button>
            </div>
          </div>
        </NeonCard>

        <NeonCard accent="green" interactive className="group">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-blue/10 border border-neon-cyan/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
              <Download className="w-6 h-6 text-neon-cyan" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-text-primary mb-1">{t('reports.csvReport')}</h3>
              <p className="text-sm text-text-secondary">{t('reports.csvReportDesc')}</p>
              <button className="neon-btn neon-btn--success neon-btn--sm mt-3">
                <Download className="w-4 h-4" /> {t('reports.export')}
              </button>
            </div>
          </div>
        </NeonCard>
      </div>

      {/* Coming Soon Notice */}
      <div className="neon-card neon-card--accent neon-card--blue">
        <p className="text-text-secondary text-sm">
          💡 {t('reports.comingSoon')}
        </p>
      </div>
    </div>
  )
}
