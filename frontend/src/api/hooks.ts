import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi, listingsApi, amazonApi, tasksApi, syncApi, bulkApi } from './endpoints'
import type { ProductListResponse, Listing } from '@/types/api'

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

// ==================== Task Keys ====================

export const taskKeys = {
  list: ['tasks'] as const,
  detail: (id: string) => ['tasks', id] as const,
}

// ==================== Product Hooks ====================

export function useProducts(params?: { status?: string; category?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: productKeys.list(params),
    queryFn: async () => {
      const { data } = await productsApi.list({ page: params?.page, page_size: params?.page_size, status: params?.status, category: params?.category })
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
      const { data } = await syncApi.syncFromAmazon()
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
