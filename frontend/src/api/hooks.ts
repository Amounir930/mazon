import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi, listingsApi, amazonApi, authApi, tasksApi, syncApi, bulkApi, exportApi } from './endpoints'
import type { ProductListResponse, Listing, SessionStatusResponse, BrowserLoginResponse } from '@/types/api'

// ==================== Product Keys ====================

export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (params?: Record<string, unknown>) => [...productKeys.lists(), params] as const,
}

// ==================== Listing Keys ====================

export const listingKeys = {
  all: ['listings'] as const,
  lists: () => [...listingKeys.all, 'list'] as const,
  list: (params?: Record<string, unknown>) => [...listingKeys.lists(), params] as const,
}

// ==================== Amazon Keys ====================

export const amazonKeys = {
  status: ['amazon', 'status'] as const,
}

export const sellerKeys = {
  info: ['sellers', 'info'] as const,
}

// ==================== Auth Keys ====================

export const authKeys = {
  session: ['auth', 'session'] as const,
  countries: ['auth', 'countries'] as const,
}

// ==================== Task Keys ====================

export const taskKeys = {
  list: ['tasks'] as const,
  detail: (id: string) => ['tasks', id] as const,
}

// ==================== Product Hooks ====================

export function useProducts(params?: { status?: string; category?: string; search?: string; seller_id?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: productKeys.list(params),
    queryFn: async () => {
      const { data } = await productsApi.list({
        page: params?.page,
        page_size: params?.page_size,
        status: params?.status,
        category: params?.category,
        search: params?.search,
        seller_id: params?.seller_id,
      })
      return data
    },
    staleTime: 1000 * 60 * 2,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const { data: result } = await productsApi.create(data as Parameters<typeof productsApi.create>[0])
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.list() })
    },
  })
}

export function useUpdateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, unknown> }) => {
      const { data: result } = await productsApi.update(id, data as Parameters<typeof productsApi.update>[1])
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
    },
  })
}

export function useDeleteProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await productsApi.delete(id)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
    },
  })
}

// ==================== Listing Hooks ====================

export function useListings(params?: { status?: string }) {
  return useQuery({
    queryKey: listingKeys.list(params),
    queryFn: async () => {
      const { data } = await listingsApi.list(params)
      return data
    },
    staleTime: 1000 * 60 * 1,
    refetchInterval: 5000,
  })
}

export function useSubmitListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (product_id: string) => {
      const { data } = await listingsApi.submit(product_id)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listingKeys.list() })
      queryClient.invalidateQueries({ queryKey: taskKeys.list })
    },
  })
}

export function useSubmitMultiListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ product_id, copies }: { product_id: string; copies: number }) => {
      const { data } = await listingsApi.submitMulti(product_id, copies)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listingKeys.list() })
      queryClient.invalidateQueries({ queryKey: taskKeys.list })
    },
  })
}

// ==================== Amazon Hooks ====================

export function useAmazonStatus() {
  return useQuery({
    queryKey: amazonKeys.status,
    queryFn: async () => {
      const { data } = await amazonApi.status()
      return data
    },
    staleTime: 1000 * 60 * 1,
    refetchInterval: 30000,
  })
}

export function useSellerInfo() {
  return useQuery({
    queryKey: sellerKeys.info,
    queryFn: async () => {
      const { data } = await sellersApi.info()
      return data
    },
    staleTime: 1000 * 60 * 5,
  })
}

export function useConnectAmazon() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: Record<string, string>) => {
      const { data: result } = await amazonApi.connect(data as Parameters<typeof amazonApi.connect>[0])
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: amazonKeys.status })
    },
  })
}

export function useVerifyConnection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { data } = await amazonApi.verify()
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: amazonKeys.status })
    },
  })
}

// ==================== Task Hooks ====================

export function useTasks() {
  return useQuery({
    queryKey: taskKeys.list,
    queryFn: async () => {
      const { data } = await tasksApi.list()
      return data
    },
    refetchInterval: 3000,
  })
}

// ==================== Sync & Bulk Hooks ====================

export function useSyncFromAmazon() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      // Get email from auth store
      const email = 'amazon_eg' // Default to current session
      const { data } = await syncApi.syncProducts(email)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
    },
  })
}

export function useBulkUpload() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (file: File) => {
      const { data } = await bulkApi.upload(file)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
    },
  })
}

// ==================== Export Hooks ====================

export function useExportPriceInventory() {
  return useMutation({
    mutationFn: async () => {
      const response = await exportApi.priceInventory()
      // Trigger file download
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'price_inventory.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      return { success: true }
    },
  })
}

export function useExportListingLoader() {
  return useMutation({
    mutationFn: async () => {
      const response = await exportApi.listingLoader()
      // Trigger file download
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'listing_loader.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      return { success: true }
    },
  })
}

// ==================== Auth Hooks (Phase 0) ====================

export function useSessionStatus() {
  return useQuery({
    queryKey: authKeys.session,
    queryFn: async () => {
      const { data } = await authApi.getSession()
      return data
    },
    staleTime: 1000 * 60 * 2,
    refetchInterval: 30000,
  })
}

export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (session_id?: string) => {
      const { data } = await authApi.logout(session_id)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.session })
    },
  })
}

export function useVerifySession() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await authApi.verifySession()
      return data
    },
  })
}

export function useSupportedCountries() {
  return useQuery({
    queryKey: authKeys.countries,
    queryFn: async () => {
      const { data } = await authApi.getSupportedCountries()
      return data
    },
    staleTime: 1000 * 60 * 60 * 24,
  })
}

export function useGetLoginUrl() {
  return useMutation({
    mutationFn: async (country_code: string) => {
      const { data } = await authApi.getLoginUrl(country_code)
      return data
    },
  })
}

export function useConnectWithCookies() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: Parameters<typeof authApi.connectWithCookies>[0]) => {
      const { data: result } = await authApi.connectWithCookies(data)
      return result
    },
    onSuccess: (data) => {
      if (data.success) {
        queryClient.invalidateQueries({ queryKey: authKeys.session })
      }
    },
  })
}

export function useDisconnectAmazon() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (email: string) => {
      const { data } = await authApi.disconnect(email)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.session })
    },
  })
}
