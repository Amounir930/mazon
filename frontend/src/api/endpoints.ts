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

  list: () =>
    api.get<{ sellers: Array<{ id: string; amazon_seller_id?: string; display_name?: string; marketplace_id?: string; is_connected: boolean }>; total: number }>('/sellers/list'),
}

// ==================== Catalog Search API ====================

export const catalogApi = {
  search: (params: { query: string; search_type: string }) =>
    api.get('/catalog/search', { params }),
  lookup: (asin: string) =>
    api.get(`/catalog/lookup/${asin}`),
}

// ==================== Products API ====================

export const productsApi = {
  list: (params?: { status?: string; category?: string; page?: number; page_size?: number }) =>
    api.get<ProductListResponse>('/products', { params }),

  get: (id: string) =>
    api.get<Product>(`/products/${id}`),

  create: (data: ProductCreate) =>
    api.post<Product>('/products', data),

  delete: (id: string) =>
    api.delete<MessageResponse>(`/products/${id}`),

  update: (id: string, data: Partial<Product>) =>
    api.put<Product>(`/products/${id}`, data),

  lookup: (productId: string, idType: string = 'EAN') =>
    api.post(`/products/lookup?product_id=${productId}&id_type=${idType}`),

  previewFeed: (data: ProductCreate) =>
    api.post('/products/preview-feed', data),

  // SP-API: Submit product to Amazon
  submitToAmazon: (productId: string) =>
    api.post(`/sp-api/submit/${productId}`),
}

// ==================== SP-API (Amazon Official) ====================

export interface SPApiListingResponse {
  success: boolean
  listing_id?: string
  submission_id?: string
  status?: string
  asin?: string
  errors?: Array<{ message: string; severity: string }>
  message?: string
}

export interface SPApiSearchResponse {
  success: boolean
  seller_id: string
  total_results: number
  items: Array<Record<string, any>>
  pagination?: { nextToken?: string }
}

export interface SPApiDeleteResponse {
  success: boolean
  status: string
  message: string
}

export interface PatchOperation {
  op: 'replace' | 'add' | 'remove'
  path: string
  value: any
}

export interface SPApiPatchRequest {
  product_type: string
  patches: PatchOperation[]
}

export interface SPApiPatchResponse {
  success: boolean
  status: string
  sku: string
  errors?: Array<{ message: string; severity: string }>
  message: string
}

export const spApi = {
  // Submit product to Amazon (existing)
  submit: (productId: string) =>
    api.post<SPApiListingResponse>(`/sp-api/submit/${productId}`),

  // Get listing status (existing)
  getListing: (sku: string) =>
    api.get(`/sp-api/listing/${sku}`),

  // Get product type schema (existing)
  getSchema: (productType: string) =>
    api.get(`/sp-api/schema/${productType}`),

  // NEW: Delete listing from Amazon
  deleteListing: (sellerId: string, sku: string) =>
    api.delete<SPApiDeleteResponse>(`/sp-api/listing/${sellerId}/${sku}`),

  // NEW: Search listings on Amazon
  searchListings: (params?: {
    seller_id?: string
    skus?: string
    status?: string
    page_size?: number
  }) => api.get<SPApiSearchResponse>('/sp-api/listings', { params }),

  // NEW: Patch listing (partial update)
  patchListing: (sellerId: string, sku: string, data: SPApiPatchRequest) =>
    api.patch<SPApiPatchResponse>(`/sp-api/listing/${sellerId}/${sku}`, data),

  // NEW: Search Amazon catalog via SP-API
  searchCatalog: (params?: {
    keywords?: string
    identifiers?: string
    page_size?: number
  }) => api.get<SPApiSearchResponse>('/sp-api/catalog/search', { params }),

  // NEW: Get catalog item by ASIN
  getCatalogItem: (asin: string) =>
    api.get(`/sp-api/catalog/${asin}`),
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
  syncProducts: () =>
    api.post('/sync/products'),

  exportToAmazon: (onlyNew: boolean = true) =>
    api.post(`/sync/export-to-amazon?only_new=${onlyNew}`),

  syncSingleProduct: (productId: string) =>
    api.post(`/sync/products/${productId}`),

  syncOrders: (days: number = 30) =>
    api.post(`/sync/orders?days=${days}`),

  syncInventory: () =>
    api.post('/sync/inventory'),
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

// ==================== Images API ====================

export const imagesApi = {
  // رفع صورة كـ file
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ url: string; filename: string; size: number; mime_type: string }>('/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // رفع صورة مباشرة (Cloudinary → GitHub fallback)
  uploadToGitHub: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<{ success: boolean; image_url: string; message: string; error: string }>('/images/upload-to-github', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // رفع صورة كـ base64
  uploadBase64: (base64Data: string) =>
    api.post<{ url: string; filename: string; size: number; mime_type: string }>('/images/upload-base64', { image: base64Data }),

  // حذف صورة
  delete: (filename: string) =>
    api.delete(`/images/static/${filename}`),

  // عرض كل الصور
  list: () =>
    api.get('/images/list'),
}

// ==================== AI Assistant API ====================

export const aiApi = {
  generate: (data: { name: string; specs: string; copies: number }) =>
    api.post<{ success: boolean; data: any; error?: string }>('/ai/generate-product', data),

  getNextModelNumber: () =>
    api.get<{ next_model_number: string }>('/ai/next-model-number'),
}
