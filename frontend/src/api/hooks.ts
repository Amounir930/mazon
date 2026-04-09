import { useQuery } from '@tanstack/react-query'
import api from '@/lib/axios'
import type { ProductListResponse, Listing } from '@/types/api'

export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (params: Record<string, any>) => [...productKeys.lists(), params] as const,
}

export const listingKeys = {
  all: ['listings'] as const,
  lists: () => [...listingKeys.all, 'list'] as const,
  list: (params: Record<string, any>) => [...listingKeys.lists(), params] as const,
}

export function useProducts(params: {
  seller_id: string
  page?: number
  status?: string
  category?: string
}) {
  return useQuery({
    queryKey: productKeys.list(params),
    queryFn: async () => {
      const { data } = await api.get<ProductListResponse>('/products', {
        params: { ...params, page_size: 50 },
      })
      return data
    },
    staleTime: 1000 * 60 * 2,
  })
}

export function useListings(params: {
  seller_id: string
  status?: string
}) {
  return useQuery({
    queryKey: listingKeys.list(params),
    queryFn: async () => {
      const { data } = await api.get<Listing[]>('/listings', {
        params: { ...params },
      })
      return data
    },
    staleTime: 1000 * 60 * 1,
  })
}

export function useStats(sellerId: string) {
  const { data: products } = useProducts({ seller_id: sellerId })
  const { data: listings } = useListings({ seller_id: sellerId })

  return {
    totalProducts: products?.total ?? 0,
    totalListings: listings?.length ?? 0,
    published: listings?.filter((l) => l.status === 'success').length ?? 0,
    queued: listings?.filter((l) => l.status === 'queued').length ?? 0,
    failed: listings?.filter((l) => l.status === 'failed').length ?? 0,
    processing: listings?.filter((l) => l.status === 'processing' || l.status === 'submitted').length ?? 0,
  }
}
