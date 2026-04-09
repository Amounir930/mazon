import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAmazonConnect } from '@/contexts/AmazonConnectContext'
import { Shield, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function AmazonConnectPage() {
  const navigate = useNavigate()
  const { connect, verify, isConnected, isLoading } = useAmazonConnect()

  const [formData, setFormData] = useState({
    lwa_client_id: '',
    lwa_client_secret: '',
    lwa_refresh_token: '',
    amazon_seller_id: '',
    display_name: 'My Amazon Store',
    marketplace_id: 'ARBP9OOSHTCHU',
  })
  const [isSaving, setIsSaving] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.lwa_client_id || !formData.lwa_client_secret ||
        !formData.lwa_refresh_token || !formData.amazon_seller_id) {
      toast.error('يرجى ملء جميع الحقول المطلوبة')
      return
    }
    setIsSaving(true)
    try {
      await connect(formData)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'فشل حفظ البيانات')
    } finally {
      setIsSaving(false)
    }
  }

  const handleVerify = async () => {
    setIsVerifying(true)
    try {
      await verify()
      setTimeout(() => navigate('/dashboard'), 1500)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error.response?.data?.detail || 'فشل الاتصال')
    } finally {
      setIsVerifying(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
      </div>
    )
  }

  if (isConnected) {
    navigate('/dashboard')
    return null
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-500/10 mb-4">
            <Shield className="w-8 h-8 text-orange-500" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">ربط حساب Amazon</h1>
          <p className="text-gray-400 text-sm">أدخل بيانات حسابك في Amazon Seller Central</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-[#12121a] rounded-2xl p-6 space-y-4 border border-gray-800/50">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Client ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.lwa_client_id}
              onChange={e => setFormData({ ...formData, lwa_client_id: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="amzn1.application-oa2-client.xxx"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Client Secret <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              value={formData.lwa_client_secret}
              onChange={e => setFormData({ ...formData, lwa_client_secret: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Refresh Token <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              value={formData.lwa_refresh_token}
              onChange={e => setFormData({ ...formData, lwa_refresh_token: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="Atzr|xxx"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Seller ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.amazon_seller_id}
              onChange={e => setFormData({ ...formData, amazon_seller_id: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="A1B2C3D4E5F6G7"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Display Name</label>
            <input
              type="text"
              value={formData.display_name}
              onChange={e => setFormData({ ...formData, display_name: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Marketplace</label>
            <select
              value={formData.marketplace_id}
              onChange={e => setFormData({ ...formData, marketplace_id: e.target.value })}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
            >
              <option value="ARBP9OOSHTCHU">مصر (Egypt)</option>
              <option value="ATVPDKIKX0DER">أمريكا (US)</option>
              <option value="A1F83G8C2ARO7P">بريطانيا (UK)</option>
              <option value="A1PA6795UKMFR9">ألمانيا (Germany)</option>
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-medium py-3 px-4 rounded-lg transition"
            >
              {isSaving ? 'جاري الحفظ...' : 'حفظ البيانات'}
            </button>
            <button
              type="button"
              onClick={handleVerify}
              disabled={isVerifying}
              className="flex-1 bg-[#1a1a2e] hover:bg-[#252540] disabled:opacity-50 text-orange-500 font-medium py-3 px-4 rounded-lg border border-orange-500/30 transition"
            >
              {isVerifying ? 'جاري التحقق...' : 'تحقق من الاتصال'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
