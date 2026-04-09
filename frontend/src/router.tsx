import { Routes, Route, Navigate, Outlet } from 'react-router-dom'

// Main pages
import DashboardPage from './pages/dashboard/DashboardPage'
import ProductListPage from './pages/products/ProductListPage'
import ProductCreatePage from './pages/products/ProductCreatePage'
import ListingQueuePage from './pages/listings/ListingQueuePage'
import ReportsPage from './pages/reports/ReportsPage'
import SettingsPage from './pages/settings/SettingsPage'

// TODO: Replace with Amazon Connect system (Phase 5)
// Temporary: simple pass-through layout until AmazonConnectContext is built
function ConnectedLayout() {
  // TODO: Check Amazon connection status
  return <Outlet />
}

export default function AppRouter() {
  // TODO: Replace with Amazon connect loading state
  return (
    <Routes>
      {/* TODO: Add /connect route for Amazon credentials page */}
      {/* Temporary: redirect /login to /dashboard */}
      <Route path="/login" element={<Navigate to="/dashboard" replace />} />
      <Route path="/register" element={<Navigate to="/dashboard" replace />} />

      {/* Main routes — TODO: protect with Amazon connection check */}
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
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

// Temporary Layout wrapper until Sidebar/Header are updated
function Layout() {
  return <Outlet />
}
