import { useAmazonStatus } from '@/contexts/AmazonConnectContext'
import { Shield, CheckCircle, AlertCircle, Globe, Loader2, RefreshCw } from 'lucide-react'
import { StatusBadge } from '@/components/common/StatusBadge'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { status, isConnected, isLoading, refreshStatus } = useAmazonStatus()

  const handleRefresh = async () => {
    try {
      await refreshStatus()
      toast.success('تم تحديث البيانات')
    } catch {
      toast.error('فشل في تحديث البيانات')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-amazon-orange animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">الإعدادات</h1>
          <p className="text-gray-400 mt-1">إعدادات الحساب والاتصال بأمازون</p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-300 transition"
        >
          <RefreshCw className="w-4 h-4" />
          تحديث
        </button>
      </div>

      {/* Connection Status */}
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-lg ${isConnected ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
              {isConnected ? <CheckCircle className="w-8 h-8" /> : <AlertCircle className="w-8 h-8" />}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                حالة الاتصال
                <StatusBadge status={isConnected ? 'success' : 'failed'} />
              </h2>
              <p className="text-gray-400 text-sm mt-1">{isConnected ? 'متصل بنجاح بأمازون' : 'غير متصل'}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <InfoCard label="Amazon Seller ID" value={status?.amazon_seller_id || '-'} icon={<Globe className="w-4 h-4" />} />
          <InfoCard label="Display Name" value={status?.display_name || '-'} icon={<Shield className="w-4 h-4" />} />
          <InfoCard label="Marketplace ID" value={status?.marketplace_id || '-'} icon={<Globe className="w-4 h-4" />} />
          <InfoCard label="Region" value={status?.region || 'EU'} icon={<Shield className="w-4 h-4" />} />
        </div>
      </div>

      {/* API Credentials (Read Only) */}
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6">
        <h2 className="text-lg font-bold text-white mb-4">بيانات الاتصال (مخزنة بأمان)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-[#0a0a0f] p-4 rounded-lg border border-gray-800">
            <label className="block text-xs font-medium text-gray-500 mb-1">Client ID</label>
            <p className="text-white font-mono text-sm">••••••••••••••••</p>
          </div>
          <div className="bg-[#0a0a0f] p-4 rounded-lg border border-gray-800">
            <label className="block text-xs font-medium text-gray-500 mb-1">Seller ID</label>
            <p className="text-white font-mono text-sm">{status?.amazon_seller_id || '-'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function InfoCard({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-[#0a0a0f] p-4 rounded-lg border border-gray-800">
      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
        {icon}
        {label}
      </div>
      <p className="text-white font-semibold text-lg">{value}</p>
    </div>
  )
}