import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Package,
  Upload,
  FileBarChart,
  Settings,
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'لوحة التحكم' },
  { to: '/products', icon: Package, label: 'المنتجات' },
  { to: '/listings', icon: Upload, label: 'طابور الرفع' },
  { to: '/reports', icon: FileBarChart, label: 'التقارير' },
  { to: '/settings', icon: Settings, label: 'الإعدادات' },
]

export default function Sidebar() {
  return (
    <aside className="fixed top-0 right-0 h-full w-64 bg-[#0d0d14] text-white z-50 border-l border-gray-800/50">
      {/* Logo */}
      <div className="flex items-center gap-3 p-6 border-b border-gray-700">
        <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
          <span className="text-xl font-bold text-white">CL</span>
        </div>
        <div>
          <h1 className="text-lg font-bold">Crazy Lister</h1>
          <p className="text-xs text-gray-400">v3.0</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                ? 'bg-orange-500 text-white font-semibold'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
