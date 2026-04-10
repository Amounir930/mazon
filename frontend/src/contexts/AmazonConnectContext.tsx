import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import api from '@/lib/axios'
import toast from 'react-hot-toast'
import type { AmazonConnectResponse } from '@/types/api'

interface AmazonConnectContextType {
  status: AmazonConnectResponse | null
  isConnected: boolean
  isLoading: boolean
  connect: (data: Record<string, string>) => Promise<void>
  verify: () => Promise<void>
  refreshStatus: () => Promise<void>
}

const AmazonConnectContext = createContext<AmazonConnectContextType | null>(null)

export function AmazonConnectProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AmazonConnectResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    refreshStatus()
  }, [])

  const refreshStatus = async () => {
    try {
      const { data } = await api.get<AmazonConnectResponse>('/amazon/status')
      setStatus(data)
    } catch {
      setStatus({
        seller_id: null,
        amazon_seller_id: null,
        is_connected: false,
        display_name: null,
        marketplace_id: null,
        last_sync_at: null,
        message: 'Not configured',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const connect = async (data: Record<string, string>) => {
    const { data: result } = await api.post<AmazonConnectResponse>('/amazon/connect', data)
    setStatus(result)
    toast.success('تم حفظ بيانات Amazon')
  }

  const verify = async () => {
    const { data } = await api.post('/amazon/verify')
    setStatus(prev => prev ? { ...prev, is_connected: true, message: data.message } : null)
    toast.success('تم الاتصال بـ Amazon بنجاح!')
  }

  return (
    <AmazonConnectContext.Provider value={{ status, isConnected: status?.is_connected ?? false, isLoading, connect, verify, refreshStatus }}>
      {children}
    </AmazonConnectContext.Provider>
  )
}

export function useAmazonConnect() {
  const context = useContext(AmazonConnectContext)
  if (!context) throw new Error('useAmazonConnect must be used within AmazonConnectProvider')
  return context
}

// Alias for SettingsPage compatibility
export const useAmazonStatus = useAmazonConnect
