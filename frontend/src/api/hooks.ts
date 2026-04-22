import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, sellersApi, productsApi, listingsApi, tasksApi, amazonApi, syncApi, bulkApi, exportApi, catalogApi, spApi, imagesApi, dashboardApi, discoveryApi, debugApi } from './endpoints'
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

// ==================== Catalog Search Keys ====================

export const catalogKeys = {
  all: ['catalog'] as const,
  search: (query: string, searchType: string) => [...catalogKeys.all, 'search', query, searchType] as const,
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

export function useProduct(id: string | undefined) {
  return useQuery({
    queryKey: ['products', 'detail', id],
    queryFn: async () => {
      if (!id) return null
      const { data } = await productsApi.get(id)
      return data
    },
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
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
      // Invalidate the entire products root to ensure list and details are refreshed
      queryClient.invalidateQueries({ queryKey: productKeys.all })
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
      queryClient.invalidateQueries({ queryKey: listingKeys.lists() })
    },
  })
}

export function useRetryListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (listing_id: string) => {
      const { data } = await listingsApi.retry(listing_id)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listingKeys.lists() })
    },
  })
}

export function useCancelListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (listing_id: string) => {
      const { data } = await listingsApi.cancel(listing_id)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listingKeys.lists() })
    },
  })
}

// ==================== Catalog Search Hooks ====================

export function useCatalogSearch() {
  return useMutation({
    mutationFn: async (params: { query: string; searchType: string }) => {
      const { data } = await catalogApi.search({
        query: params.query,
        search_type: params.searchType,
      })
      return data
    },
  })
}

export function useCatalogLookup(asin: string) {
  return useQuery({
    queryKey: catalogKeys.search(asin, 'ASIN'),
    queryFn: async () => {
      const { data } = await catalogApi.lookup(asin)
      return data
    },
    enabled: !!asin,
    staleTime: 1000 * 60 * 5,
  })
}

// ==================== Seller Hooks ====================

export function useSellerInfo() {
  return useQuery({
    queryKey: sellerKeys.info,
    queryFn: async () => {
      const { data } = await sellersApi.info()
      return data
    },
    staleTime: 1000 * 60 * 5,
    retry: 2,
  })
}

export function useSellersList() {
  return useQuery({
    queryKey: ['sellers', 'list'],
    queryFn: async () => {
      const { data } = await sellersApi.list()
      return data
    },
    staleTime: 1000 * 60 * 2,
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
      const { data } = await syncApi.syncProducts()
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
    },
  })
}

export function useExportToAmazon() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (onlyNew: boolean = true) => {
      const { data } = await syncApi.exportToAmazon(onlyNew)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listingKeys.lists() })
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

// ==================== SP-API Hooks (Amazon Official) ====================

export const spApiKeys = {
  listing: (sku: string) => ['sp-api', 'listing', sku] as const,
  listings: (params?: Record<string, unknown>) => ['sp-api', 'listings', params] as const,
  catalog: (params?: Record<string, unknown>) => ['sp-api', 'catalog', params] as const,
  catalogItem: (asin: string) => ['sp-api', 'catalog', asin] as const,
}

export function useSPApiListing(sku: string) {
  return useQuery({
    queryKey: spApiKeys.listing(sku),
    queryFn: async () => {
      const { data } = await spApi.getListing(sku)
      return data
    },
    enabled: !!sku,
    staleTime: 1000 * 60 * 1,
  })
}

export function useDeleteListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ sellerId, sku }: { sellerId: string; sku: string }) => {
      const { data } = await spApi.deleteListing(sellerId, sku)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: spApiKeys.listings() })
      queryClient.invalidateQueries({ queryKey: listingKeys.lists() })
    },
  })
}

export function useSearchListings(params?: {
  seller_id?: string
  skus?: string
  status?: string
  page_size?: number
}) {
  return useQuery({
    queryKey: spApiKeys.listings(params),
    queryFn: async () => {
      const { data } = await spApi.searchListings(params)
      return data
    },
    staleTime: 1000 * 60 * 1,
  })
}

export function usePatchListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      sellerId,
      sku,
      data,
    }: {
      sellerId: string
      sku: string
      data: { product_type: string; patches: Array<{ op: string; path: string; value: any }> }
    }) => {
      const { data: result } = await spApi.patchListing(sellerId, sku, data)
      return result
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: spApiKeys.listings() })
      queryClient.invalidateQueries({ queryKey: spApiKeys.listing(variables.sku) })
      queryClient.invalidateQueries({ queryKey: listingKeys.lists() })
    },
  })
}

export function useSearchCatalogSPApi(params?: {
  keywords?: string
  identifiers?: string
  page_size?: number
}) {
  // Stable query key — serialize params to avoid infinite refetches
  const queryKey = ['sp-api', 'catalog', params?.keywords, params?.identifiers, params?.page_size] as const

  return useQuery({
    queryKey,
    queryFn: async () => {
      const { data } = await spApi.searchCatalog(params)
      return data
    },
    enabled: !!(params?.keywords || params?.identifiers),
    staleTime: 1000 * 60 * 5,
  })
}

export function useCatalogItemSPApi(asin: string) {
  return useQuery({
    queryKey: spApiKeys.catalogItem(asin),
    queryFn: async () => {
      const { data } = await spApi.getCatalogItem(asin)
      return data
    },
    enabled: !!asin,
    staleTime: 1000 * 60 * 5,
  })
}

// ==================== Dashboard Hooks ====================

export function useDashboardMetrics(days: number = 30) {
  return useQuery({
    queryKey: ['dashboard', 'metrics', days],
    queryFn: async () => {
      const { data } = await dashboardApi.getMetrics(days)
      return data.data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useSyncDashboard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { data } = await dashboardApi.sync()
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'metrics'] })
    },
  })
}

// ==================== Discovery Hooks ====================

export function useDiscovery(keywords: string = "bestsellers") {
  return useQuery({
    queryKey: ['discovery', 'top-items', keywords],
    queryFn: async () => {
      const { data } = await discoveryApi.getTopItems(keywords)
      return data.data
    },
    staleTime: 1000 * 60 * 30, // 30 minutes
  })
}

// ==================== Debug Hooks ====================

export function useLogs(lines: number = 100, enabled: boolean = false) {
  return useQuery({
    queryKey: ['debug', 'logs', lines],
    queryFn: async () => {
      const { data } = await debugApi.getLogs(lines)
      return data
    },
    enabled,
    refetchInterval: 3000, // Poll every 3 seconds
  })
}

