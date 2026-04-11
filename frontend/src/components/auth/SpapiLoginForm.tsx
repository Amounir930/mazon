import { useState } from 'react'
import { useSpapiLogin } from '@/api/hooks'
import { Key, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface SpapiLoginFormProps {
  onSuccess?: () => void
}

export function SpapiLoginForm({ onSuccess }: SpapiLoginFormProps) {
  const [formData, setFormData] = useState({
    lwa_client_id: '',
    lwa_client_secret: '',
    lwa_refresh_token: '',
    marketplace_id: 'ARBP9OOSHTCHU',
    aws_access_key: '',
    aws_secret_key: '',
  })

  const mutation = useSpapiLogin()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.lwa_client_id || !formData.lwa_client_secret || !formData.lwa_refresh_token) {
      toast.error('يرجى ملء الحقول الثلاثة المطلوبة (Client ID, Secret, Refresh Token)')
      return
    }

    try {
      await mutation.mutateAsync(formData)
      toast.success('تم حفظ بيانات SP-API بنجاح!')
      onSuccess?.()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل حفظ البيانات')
    }
  }

  const isLoading = mutation.isPending

  return (
    <div className="space-y-6">
      {/* Method Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
          <Key className="w-5 h-5 text-orange-400" />
        </div>
        <div>
          <h3 className="text-white font-bold">SP-API الرسمية (OAuth2)</h3>
          <p className="text-gray-400 text-xs">آمنة 100% • تحتاج إعداد مسبق</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Client ID */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">LWA Client ID *</label>
          <input
            type="text"
            value={formData.lwa_client_id}
            onChange={e => setFormData({ ...formData, lwa_client_id: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none font-mono text-sm"
            placeholder="amzn1.application-oa2-client.xxx"
            disabled={isLoading}
          />
        </div>

        {/* Client Secret */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">LWA Client Secret *</label>
          <input
            type="password"
            value={formData.lwa_client_secret}
            onChange={e => setFormData({ ...formData, lwa_client_secret: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none font-mono text-sm"
            placeholder="••••••••"
            disabled={isLoading}
          />
        </div>

        {/* Refresh Token */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">LWA Refresh Token *</label>
          <input
            type="password"
            value={formData.lwa_refresh_token}
            onChange={e => setFormData({ ...formData, lwa_refresh_token: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none font-mono text-sm"
            placeholder="Atzr|IwEBI..."
            disabled={isLoading}
          />
        </div>

        {/* Marketplace ID */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Marketplace ID</label>
          <select
            value={formData.marketplace_id}
            onChange={e => setFormData({ ...formData, marketplace_id: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none"
            disabled={isLoading}
          >
            <option value="ARBP9OOSHTCHU">🇪🇬 مصر (ARBP9OOSHTCHU)</option>
            <option value="ATVPDKIKX0DER">🇺🇸 أمريكا (ATVPDKIKX0DER)</option>
            <option value="A1F83G8C2ARO7P">🇬🇧 بريطانيا (A1F83G8C2ARO7P)</option>
            <option value="A1PA6795UKMFR9">🇩🇪 ألمانيا (A1PA6795UKMFR9)</option>
            <option value="A2NODRKZP88ZB9">🇸🇦 السعودية (A2NODRKZP88ZB9)</option>
            <option value="A9DR927O4KPT0">🇦🇪 الإمارات (A9DR927O4KPT0)</option>
          </select>
        </div>

        {/* AWS Access Key */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">AWS Access Key (اختياري)</label>
          <input
            type="text"
            value={formData.aws_access_key}
            onChange={e => setFormData({ ...formData, aws_access_key: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none font-mono text-sm"
            placeholder="AKIA..."
            disabled={isLoading}
          />
        </div>

        {/* AWS Secret Key */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">AWS Secret Key (اختياري)</label>
          <input
            type="password"
            value={formData.aws_secret_key}
            onChange={e => setFormData({ ...formData, aws_secret_key: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none font-mono text-sm"
            placeholder="••••••••"
            disabled={isLoading}
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white font-bold py-3 rounded-lg transition flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              جاري الحفظ...
            </>
          ) : (
            'حفظ والاتصال'
          )}
        </button>

        <div className="bg-gray-800/50 rounded-lg p-3 text-xs text-gray-400">
          <p className="font-bold mb-1">📋 كيفية الحصول على البيانات:</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>روح <a href="https://developer.amazonservices.com" target="_blank" className="text-orange-400 hover:underline">developer.amazonservices.com</a></li>
            <li>سجّل تطبيق جديد (SP-API Application)</li>
            <li>انسخ Client ID + Client Secret</li>
            <li>عمل Self-Authorization تاخد Refresh Token</li>
          </ol>
        </div>
      </form>
    </div>
  )
}
