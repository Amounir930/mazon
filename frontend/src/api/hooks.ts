import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi, listingsApi, authApi } from './endpoints'
import type {
  ProductListResponse,
  Listing,
  ProductCreate,
  LoginRequest,
  RegisterRequest,
  Seller,
} from '@/types/api'

// ==================== Product Keys ====================

export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (params: Record<string, unknown>) => [...productKeys.lists(), params] as const,
  details: () => [...productKeys.all, 'detail'] as const,
  detail: (id: string) => [...productKeys.details(), id] as const,
}

// ==================== Listing Keys ====================

export const listingKeys = {
  all: ['listings'] as const,
  lists: () => [...listingKeys.all, 'list'] as const,
  list: (params: Record<string, unknown>) => [...listingKeys.lists(), params] as const,
}

// ==================== Auth Keys ====================

export const authKeys = {
  me: ['auth', 'me'] as const,
}

// ==================== Product Hooks ====================

export function useProducts(params: {
  seller_id: string
  page?: number
  status?: string
  category?: string
}) {
  return useQuery({
    queryKey: productKeys.list(params),
    queryFn: async () => {
      const { data } = await productsApi.list({ ...params, page_size: 50 })
      return data
    },
    staleTime: 1000 * 60 * 2,
  })
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: productKeys.detail(id),
    queryFn: async () => {
      const { data } = await productsApi.get(id)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ product, seller_id }: { product: ProductCreate; seller_id: string }) => {
      const { data } = await productsApi.create(product, seller_id)
      return data
    },
    onSuccess: (_, { seller_id }) => {
      queryClient.invalidateQueries({ queryKey: productKeys.list({ seller_id }) })
    },
  })
}

export function useUpdateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<ProductCreate> }) => {
      const { data: result } = await productsApi.update(id, data)
      return result
    },
    onSuccess: (product) => {
      queryClient.invalidateQueries({ queryKey: productKeys.detail(product.id) })
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

export function useListings(params: { seller_id: string; status?: string }) {
  return useQuery({
    queryKey: listingKeys.list(params),
    queryFn: async () => {
      const { data } = await listingsApi.list(params)
      return data
    },
    staleTime: 1000 * 60 * 1,
  })
}

export function useSubmitListing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: { product_id: string; seller_id: string }) => {
      const { data: result } = await listingsApi.submit(data)
      return result
    },
    onSuccess: (_, { seller_id }) => {
      queryClient.invalidateQueries({ queryKey: listingKeys.list({ seller_id }) })
    },
  })
}

// ==================== Auth Hooks ====================

export function useMe() {
  return useQuery({
    queryKey: authKeys.me,
    queryFn: async () => {
      const { data } = await authApi.getMe()
      return data
    },
    retry: false,
  })
}

export function useLogin() {
  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const { data: result } = await authApi.login(data)
      return result
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      const { data: result } = await authApi.register(data)
      return result
    },
  })
}

// ==================== Stats Hook ====================

export function useStats(sellerId: string) {
  const { data: products } = useProducts({ seller_id: sellerId })
  const { data: listings } = useListings({ seller_id: sellerId })

  return {
    totalProducts: products?.total ?? 0,
    totalListings: listings?.length ?? 0,
    published: listings?.filter((l: Listing) => l.status === 'success').length ?? 0,
    queued: listings?.filter((l: Listing) => l.status === 'queued').length ?? 0,
    failed: listings?.filter((l: Listing) => l.status === 'failed').length ?? 0,
    processing: listings?.filter((l: Listing) => l.status === 'processing' || l.status === 'submitted').length ?? 0,
  }
}
