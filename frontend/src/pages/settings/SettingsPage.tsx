import { useState, useEffect } from 'react'
import { useAmazonStatus, useConnectAmazon, useVerifyConnection } from '@/api/hooks'
import { Shield, CheckCircle, AlertCircle, Globe, Loader2, Save, Key } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { status, isConnected, isLoading, refreshStatus } = useAmazonStatus()
  const connectMutation = useConnectAmazon()
  const verifyMutation = useVerifyConnection()

  const [formData, setFormData] = useState({
    lwa_client_id: '',
    lwa_client_secret: '',
    lwa_refresh_token: '',
    amazon_seller_id: '',
    display_name: '',
    marketplace_id: 'ARBP9OOSHTCHU'
  })

  const [mode, setMode] = useState<'view' | 'edit'>('view')

  // Load existing data when connected
  useEffect(() => {
    if (status && isConnected && mode === 'view') {
      setFormData(prev => ({
        ...prev,
        lwa_client_id: '', // Never show full secret in edit mode for security
        lwa_client_secret: '',
        lwa_refresh_token: '',
        amazon_seller_id: status.amazon_seller_id || '',
        display_name: status.display_name || ''
      }))
    }
  }, [status, isConnected])

  const handleSaveAndConnect = async () => {
    if (!formData.lwa_client_id || !formData.amazon_seller_id) {
      toast.error('يرجى إدخال Client ID و Seller ID على الأقل')
      return
    }

    try {
      // 1. Save Credentials
      await connectMutation.mutateAsync({
        lwa_client_id: formData.lwa_client_id,
        lwa_client_secret: formData.lwa_client_secret || '********',
        lwa_refresh_token: formData.lwa_refresh_token || '********',
        amazon_seller_id: formData.amazon_seller_id,
        display_name: formData.display_name || 'My Store',
        marketplace_id: formData.marketplace_id
      })

      // 2. Verify Connection
      await verifyMutation.mutateAsync()

      // 3. FORCE UI UPDATE: Fetch fresh status immediately
      await refreshStatus()

      toast.success('تم حفظ البيانات والاتصال بنجاح!')
      setMode('view')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل الاتصال. تأكد من البيانات.')
    }
  }

  const handleManualVerify = async () => {
    try {
      await verifyMutation.mutateAsync()
    } catch (error: any) {
      toast.error('فشل التحقق: ' + (error.response?.data?.detail || 'غير متصل'))
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
    <div className="space-y-6 max-w-4xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">إعدادات التاجر (Amazon Seller)</h1>
          <p className="text-gray-400 mt-1">قم بإدخال بيانات Amazon LWA الخاصة بك للبدء</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMode(mode === 'view' ? 'edit' : 'view')}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-300 flex items-center gap-2 transition"
          >
            {mode === 'view' ? '✏️ تعديل البيانات' : '👁️ عرض فقط'}
          </button>
        </div>
      </div>

      {/* Connection Status Banner */}
      <div className={`p-4 rounded-xl border flex items-center justify-between ${isConnected ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
        <div className="flex items-center gap-3">
          {isConnected ? <CheckCircle className="w-6 h-6 text-green-500" /> : <AlertCircle className="w-6 h-6 text-red-500" />}
          <div>
            <h3 className={`font-bold ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              {isConnected ? 'متصل بـ Amazon SP-API' : 'غير متصل'}
            </h3>
            <p className="text-xs text-gray-400">
              {isConnected ? `Seller ID: ${status?.amazon_seller_id}` : 'يجب إدخال البيانات والضغط على حفظ'}
            </p>
          </div>
        </div>
        {isConnected && (
          <button onClick={handleManualVerify} className="text-sm text-green-400 hover:text-green-300 underline">
            إعادة التحقق
          </button>
        )}
      </div>

      {/* Form Card */}
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-6">

        {/* Editable Fields Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Client ID */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <Key className="w-4 h-4" /> LWA Client ID
            </label>
            {mode === 'edit' ? (
              <input
                type="text"
                placeholder="amzn1.application-oa2-client..."
                value={formData.lwa_client_id}
                onChange={(e) => setFormData({ ...formData, lwa_client_id: e.target.value })}
                className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-amazon-orange outline-none"
              />
            ) : (
              <div className="w-full bg-[#0a0a0f] border border-gray-800 rounded-lg px-4 py-2 text-gray-500">
                ••••••••••••••••
              </div>
            )}
          </div>

          {/* Client Secret */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-400">LWA Client Secret</label>
            {mode === 'edit' ? (
              <input
                type="password"
                placeholder="Client Secret"
                value={formData.lwa_client_secret}
                onChange={(e) => setFormData({ ...formData, lwa_client_secret: e.target.value })}
                className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-amazon-orange outline-none"
              />
            ) : (
              <div className="w-full bg-[#0a0a0f] border border-gray-800 rounded-lg px-4 py-2 text-gray-500">
                ••••••••••••••••
              </div>
            )}
          </div>

          {/* Refresh Token */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-400">Refresh Token</label>
            {mode === 'edit' ? (
              <input
                type="password"
                placeholder="Atzr|IwEBI..."
                value={formData.lwa_refresh_token}
                onChange={(e) => setFormData({ ...formData, lwa_refresh_token: e.target.value })}
                className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-amazon-orange outline-none"
              />
            ) : (
              <div className="w-full bg-[#0a0a0f] border border-gray-800 rounded-lg px-4 py-2 text-gray-500 truncate">
                Atzr|••••••••••••••••
              </div>
            )}
          </div>

          {/* Seller ID */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-400">Amazon Seller ID</label>
            {mode === 'edit' ? (
              <input
                type="text"
                placeholder="A2EXAMPLE123"
                value={formData.amazon_seller_id}
                onChange={(e) => setFormData({ ...formData, amazon_seller_id: e.target.value })}
                className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-amazon-orange outline-none"
              />
            ) : (
              <div className="w-full bg-[#0a0a0f] border border-gray-800 rounded-lg px-4 py-2 text-gray-500 font-mono">
                {status?.amazon_seller_id || 'غير محدد'}
              </div>
            )}
          </div>

        </div>

        {/* Action Buttons */}
        {mode === 'edit' && (
          <div className="pt-4 border-t border-gray-800 flex gap-4">
            <button
              onClick={handleSaveAndConnect}
              disabled={connectMutation.isPending}
              className="flex-1 bg-amazon-orange hover:bg-orange-600 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition disabled:opacity-50"
            >
              {connectMutation.isPending ? <Loader2 className="animate-spin w-5 h-5" /> : <Save className="w-5 h-5" />}
              حفظ البيانات والاتصال
            </button>
            <button
              onClick={() => setMode('view')}
              className="px-6 py-3 border border-gray-700 rounded-lg text-gray-400 hover:text-white"
            >
              إلغاء
            </button>
          </div>
        )}

        {/* Read-Only Info */}
        <div className="grid grid-cols-2 gap-4 pt-4">
          <div className="bg-[#0a0a0f] p-3 rounded border border-gray-800">
            <span className="text-xs text-gray-500 block">Display Name</span>
            <span className="text-white text-sm">{status?.display_name || '---'}</span>
          </div>
          <div className="bg-[#0a0a0f] p-3 rounded border border-gray-800">
            <span className="text-xs text-gray-500 block">Marketplace ID</span>
            <span className="text-white text-sm font-mono">{status?.marketplace_id || '---'}</span>
          </div>
        </div>

      </div>
    </div>
  )
}