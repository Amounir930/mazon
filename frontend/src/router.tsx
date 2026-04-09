import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAmazonConnect } from './contexts/AmazonConnectContext'
import Layout from './components/layout/Layout'

// Amazon connect
import AmazonConnectPage from './pages/amazon/AmazonConnectPage'

// Main pages
import DashboardPage from './pages/dashboard/DashboardPage'
import ProductListPage from './pages/products/ProductListPage'
import ProductCreatePage from './pages/products/ProductCreatePage'
import ListingQueuePage from './pages/listings/ListingQueuePage'
import ReportsPage from './pages/reports/ReportsPage'
import SettingsPage from './pages/settings/SettingsPage'

// Connected layout — guards all child routes
function ConnectedLayout() {
  const { isConnected, isLoading } = useAmazonConnect()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0a0f]">
        <div className="w-10 h-10 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isConnected) {
    return <Navigate to="/connect" replace />
  }

  return <Outlet />
}

export default function AppRouter() {
  return (
    <Routes>
      {/* Amazon connect — always accessible */}
      <Route path="/connect" element={<AmazonConnectPage />} />

      {/* Protected routes — require Amazon connection */}
      <Route element={<ConnectedLayout />}>
        <Route element={<Layout />}>
          <Route path="" element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="products" element={<ProductListPage />} />
          <Route path="products/create" element={<ProductCreatePage />} />
          <Route path="listings" element={<ListingQueuePage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/connect" replace />} />
    </Routes>
  )
}
