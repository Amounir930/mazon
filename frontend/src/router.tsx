import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import Layout from './components/layout/Layout'

import DashboardPage from './pages/dashboard/DashboardPage'
import ProductListPage from './pages/products/ProductListPage'
import ProductCreatePage from './pages/products/ProductCreatePage'
import ListingQueuePage from './pages/listings/ListingQueuePage'
import ReportsPage from './pages/reports/ReportsPage'
import SettingsPage from './pages/settings/SettingsPage'

function ConnectedLayout() {
  return <Outlet />
}

export default function AppRouter() {
  return (
    <Routes>
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
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
