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

// ==================== Auth API (Phase 0 - New) ====================

export interface SessionStatusResponse {
  is_connected: boolean
  auth_method?: string
  seller_name?: string
  email?: string
  country_code?: string
  marketplace_id?: string
  is_valid: boolean
  last_verified_at?: string
}

export interface CookieConnectRequest {
  email: string
  cookies: Array<Record<string, any>>
  country_code: string
  seller_name?: string
}

export interface CookieConnectResponse {
  success: boolean
  seller_name?: string
  country_code?: string
  session_id?: string
  error?: string
  message?: string
}

export const authApi = {
  getLoginUrl: (country_code = 'eg') =>
    api.get<{ success: boolean; login_url: string; country_code: string }>('/auth/login-url', { params: { country_code } }),

  connectWithCookies: (data: CookieConnectRequest) =>
    api.post<CookieConnectResponse>('/auth/connect', data),

  disconnect: (email: string) =>
    api.post<{ success: boolean; message: string }>('/auth/disconnect', { email }),

  getSession: () =>
    api.get<SessionStatusResponse>('/auth/status'),  // Changed from /session to /status

  verifySession: () =>
    api.post<SessionStatusResponse>('/auth/verify-session'),

  logout: (session_id?: string) =>
    api.post('/auth/logout', null, { params: { session_id } }),

  getSupportedCountries: () =>
    api.get<{ countries: Record<string, string> }>('/auth/supported-countries'),
}

// ==================== Sellers API ====================

export const sellersApi = {
  info: () =>
    api.get('/sellers/info'),
}

// ==================== Products API ====================

export const productsApi = {
  list: (params?: { status?: string; category?: string; page?: number; page_size?: number }) =>
    api.get<ProductListResponse>('/products', { params }),

  create: (data: ProductCreate) =>
    api.post<Product>('/products', data),

  delete: (id: string) =>
    api.delete<MessageResponse>(`/products/${id}`),

  update: (id: string, data: Partial<Product>) =>
    api.put<Product>(`/products/${id}`, data),
}

// ==================== Listings API ====================

export const listingsApi = {
  list: (params?: { status?: string }) =>
    api.get<Listing[]>('/listings', { params }),

  submit: (product_id: string) =>
    api.post('/listings/submit', null, { params: { product_id } }),

  submitMulti: (product_id: string, copies: number) =>
    api.post('/listings/submit-multi', null, { params: { product_id, copies } }),

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

// ==================== Export API ====================

export const exportApi = {
  priceInventory: () =>
    api.post('/export/price-inventory', null, { responseType: 'blob' }),

  listingLoader: () =>
    api.post('/export/listing-loader', null, { responseType: 'blob' }),
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
