import api from '@/lib/axios'
import type {
  AmazonConnectRequest,
  AmazonConnectResponse,
  AmazonVerifyResponse,
  Product,
  ProductCreate,
  ProductListResponse,
  Listing,
  TaskStatus,
  MessageResponse,
} from '@/types/api'

// ==================== Amazon API ====================

export const amazonApi = {
  connect: (data: AmazonConnectRequest) =>
    api.post<AmazonConnectResponse>('/amazon/connect', data),

  verify: () =>
    api.post<AmazonVerifyResponse>('/amazon/verify'),

  status: () =>
    api.get<AmazonConnectResponse>('/amazon/status'),
}

// ==================== Products API ====================

export const productsApi = {
  list: (params?: { status?: string; category?: string; page?: number; page_size?: number }) =>
    api.get<ProductListResponse>('/products', { params }),

  create: (data: ProductCreate) =>
    api.post<Product>('/products', data),

  delete: (id: string) =>
    api.delete<MessageResponse>(`/products/${id}`),
}

// ==================== Listings API ====================

export const listingsApi = {
  list: (params?: { status?: string }) =>
    api.get<Listing[]>('/listings', { params }),

  submit: (product_id: string) =>
    api.post('/listings/submit', null, { params: { product_id } }),

  retry: (listing_id: string) =>
    api.post(`/listings/${listing_id}/retry`),
}

// ==================== Tasks API ====================

export const tasksApi = {
  get: (id: string) =>
    api.get<TaskStatus>(`/tasks/${id}`),

  list: () =>
    api.get<Record<string, TaskStatus>>('/tasks/'),
}

// ==================== Sync API ====================

export const syncApi = {
  syncFromAmazon: () =>
    api.post('/sync'),
}

// ==================== Bulk API ====================

export const bulkApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/bulk/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
