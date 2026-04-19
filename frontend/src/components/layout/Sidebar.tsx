import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Package, List, FileText, Settings, Search, LogOut, AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { LanguageSwitcher } from '@/components/common'
import { useSessionStatus, useLogout } from '@/api/hooks'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import logo from '@/assets/logo.png'

export default function Sidebar() {
  const { t } = useTranslation()
  const { data: session, isLoading, refetch } = useSessionStatus()
  const logoutMutation = useLogout()
  const [lastCheck, setLastCheck] = useState(Date.now())

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      refetch()
      setLastCheck(Date.now())
    }, 5 * 60 * 1000) // 5 minutes
    return () => clearInterval(interval)
  }, [refetch])

  // Auto-logout on connection failure
  useEffect(() => {
    if (session && !session.is_connected && lastCheck < Date.now() - 30000) {
      // Only auto-logout if it's been more than 30s since last check
      toast.error(t('settings.disconnected'))
    }
  }, [session, lastCheck, t])

  const handleLogout = async () => {
    try {
      await logoutMutation.mutateAsync()
      toast.success(t('settings.logoutSuccess'))
      refetch()
    } catch {
      toast.error(t('settings.saveError'))
    }
  }

  const isConnected = session?.is_connected
  const sellerName = session?.seller_name

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
            <div className="w-10 h-10 rounded-xl bg-amazon-orange/10 flex items-center justify-center shadow-lg overflow-hidden border border-amazon-orange/20 p-1">
              <img src={logo} alt="Logo" className="w-full h-full object-contain" />
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

      {/* Connection Status Footer */}
      <div className="p-4 border-t border-border-subtle">
        {isLoading ? (
          <div className="px-4 py-3 rounded-xl bg-bg-elevated/50 border border-border-subtle flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></div>
            <span className="text-xs text-text-muted">{t('common.loading')}</span>
          </div>
        ) : isConnected ? (
          <div className="space-y-2">
            <div className="px-4 py-3 rounded-xl bg-green-500/10 border border-green-500/30">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                <span className="text-xs text-green-400 font-medium">{t('common.connected')}</span>
              </div>
              {sellerName && (
                <p className="text-xs text-text-muted mt-1 font-mono truncate" dir="ltr">{sellerName}</p>
              )}
            </div>
            <button
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs hover:bg-red-500/20 transition-colors disabled:opacity-50"
            >
              <LogOut className="w-3 h-3" />
              {logoutMutation.isPending ? t('common.loading') : t('settings.logout')}
            </button>
          </div>
        ) : (
          <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3 h-3 text-red-400" />
              <span className="text-xs text-red-400 font-medium">{t('common.disconnected')}</span>
            </div>
            <p className="text-xs text-text-muted mt-1">{t('settings.disconnectedDesc')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
