import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Package, List, FileText, Settings, Search } from 'lucide-react'

const menuItems = [
  { to: '/dashboard', label: 'لوحة التحكم', icon: LayoutDashboard },
  { to: '/products', label: 'المنتجات', icon: Package },
  { to: '/products/search', label: 'البحث في Amazon', icon: Search },
  { to: '/listings', label: 'طابور الرفع', icon: List },
  { to: '/reports', label: 'التقارير', icon: FileText },
  { to: '/settings', label: 'الاتصال والإعدادات', icon: Settings },
]

export default function Sidebar() {
  return (
    <div className="w-64 bg-[#12121a] border-r border-gray-800/50 h-screen flex flex-col">
      <div className="p-6 border-b border-gray-800/50">
        <h1 className="text-xl font-bold text-white">Crazy Lister <span className="text-orange-500">v3.0</span></h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/dashboard'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive ? 'bg-orange-500/10 text-orange-500' : 'text-gray-400 hover:bg-gray-800/50 hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
