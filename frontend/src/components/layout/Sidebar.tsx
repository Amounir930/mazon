import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Package,
  Upload,
  FileBarChart,
  Settings,
  LogOut,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'لوحة التحكم' },
  { to: '/products', icon: Package, label: 'المنتجات' },
  { to: '/listings', icon: Upload, label: 'طابور الرفع' },
  { to: '/reports', icon: FileBarChart, label: 'التقارير' },
  { to: '/settings', icon: Settings, label: 'الإعدادات' },
]

export default function Sidebar() {
  const { logout } = useAuth()

  return (
    <aside className="fixed top-0 right-0 h-full w-64 bg-amazon-blue text-white z-50">
      {/* Logo */}
      <div className="flex items-center gap-3 p-6 border-b border-gray-700">
        <div className="w-10 h-10 bg-amazon-orange rounded-lg flex items-center justify-center">
          <span className="text-xl font-bold text-amazon-dark">CL</span>
        </div>
        <div>
          <h1 className="text-lg font-bold">Crazy Lister</h1>
          <p className="text-xs text-gray-400">v2.0</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-amazon-orange text-amazon-dark font-semibold'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="absolute bottom-0 right-0 left-0 p-4 border-t border-gray-700">
        <button
          onClick={logout}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-gray-300 hover:bg-red-600 hover:text-white transition-colors"
        >
          <LogOut className="w-5 h-5" />
          <span>تسجيل الخروج</span>
        </button>
      </div>
    </aside>
  )
}
