import { useAmazonConnect } from '@/contexts/AmazonConnectContext'
import { Shield } from 'lucide-react'

export default function Header() {
  const { status } = useAmazonConnect()

  return (
    <header className="bg-[#12121a] border-b border-gray-800/50 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Crazy Lister</h2>
          <p className="text-sm text-gray-400">Amazon Auto-Listing System v3.0</p>
        </div>
        <div className="flex items-center gap-4">
          {status && (
            <div className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] rounded-lg border border-gray-700/50">
              <Shield className={`w-4 h-4 ${status.is_connected ? 'text-green-400' : 'text-gray-500'}`} />
              <span className="text-sm text-gray-300">{status.display_name || status.amazon_seller_id || 'Not configured'}</span>
              <span className={`w-2 h-2 rounded-full ${status.is_connected ? 'bg-green-400' : 'bg-gray-500'}`} />
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
