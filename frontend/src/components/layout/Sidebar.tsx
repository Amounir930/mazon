import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Package, List, FileText, Settings, Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { LanguageSwitcher } from '@/components/common'

export default function Sidebar() {
  const { t } = useTranslation()

  const menuItems = [
    { to: '/dashboard', label: t('sidebar.dashboard'), icon: LayoutDashboard },
    { to: '/products', label: t('sidebar.products'), icon: Package },
    { to: '/products/search', label: t('sidebar.searchAmazon'), icon: Search },
    { to: '/listings', label: t('sidebar.listingQueue'), icon: List },
    { to: '/reports', label: t('sidebar.reports'), icon: FileText },
    { to: '/settings', label: t('sidebar.settings'), icon: Settings },
  ]

  return (
    <div className="w-64 bg-bg-tertiary/80 backdrop-blur-xl border-r border-border-subtle h-screen flex flex-col contain-layout">
      {/* Logo Section */}
      <div className="p-6 border-b border-border-subtle">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amazon-orange to-amazon-light flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">C</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-text-primary">{t('app.name')}</h1>
              <span className="text-xs text-amazon-orange font-medium">{t('app.version')}</span>
            </div>
          </div>
          <LanguageSwitcher />
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/dashboard'}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive 
                  ? 'bg-gradient-to-r from-amazon-orange/20 to-amazon-light/10 text-amazon-orange border border-amazon-orange/30 shadow-lg shadow-amazon-orange/10' 
                  : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary border border-transparent'
              }`
            }
          >
            <Icon className="w-5 h-5 transition-transform duration-200 group-hover:scale-110" />
            <span className="font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>
      
      {/* Footer */}
      <div className="p-4 border-t border-border-subtle">
        <div className="px-4 py-3 rounded-xl bg-bg-elevated/50 border border-border-subtle">
          <p className="text-xs text-text-muted">{t('common.status')}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse"></span>
            <span className="text-xs text-text-secondary">{t('common.connected')}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
