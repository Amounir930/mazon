import api from '@/lib/axios'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  Seller,
  Product,
  ProductCreate,
  ProductListResponse,
  Listing,
  MessageResponse,
} from '@/types/api'

// ==================== Auth API ====================

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/auth/login', data),

  register: (data: RegisterRequest) =>
    api.post<RegisterResponse>('/auth/register', data),

  getMe: () =>
    api.get<Seller>('/auth/me'),

  logout: () =>
    api.post<MessageResponse>('/auth/logout'),
}

// ==================== Products API ====================

export const productsApi = {
  list: (params: {
    seller_id: string
    status?: string
    category?: string
    page?: number
    page_size?: number
  }) => api.get<ProductListResponse>('/products', { params }),

  get: (id: string) =>
    api.get<Product>(`/products/${id}`),

  create: (data: ProductCreate, seller_id: string) =>
    api.post<Product>('/products', data, { params: { seller_id } }),

  update: (id: string, data: Partial<ProductCreate>) =>
    api.put<Product>(`/products/${id}`, data),

  delete: (id: string) =>
    api.delete<MessageResponse>(`/products/${id}`),

  bulkCreate: (products: ProductCreate[], seller_id: string) =>
    api.post<Product[]>('/products/bulk-create', products, { params: { seller_id } }),

  optimize: (id: string) =>
    api.post(`/products/${id}/optimize`),
}

// ==================== Listings API ====================

export const listingsApi = {
  list: (params: { seller_id: string; status?: string }) =>
    api.get<Listing[]>('/listings', { params }),

  submit: (data: { product_id: string; seller_id: string }) =>
    api.post<Listing>('/listings/submit', data),

  get: (id: string) =>
    api.get<Listing>(`/listings/${id}`),

  getResults: (seller_id: string) =>
    api.get('/listings/results', { params: { seller_id } }),

  retry: (id: string) =>
    api.post<Listing>(`/listings/${id}/retry`),
}

// ==================== Sellers API ====================

export const sellersApi = {
  register: (data: {
    email: string
    seller_id: string
    marketplace_id: string
    region: string
    lwa_refresh_token: string
  }) => api.post<Seller>('/sellers/register', data),

  get: (id: string) =>
    api.get<Seller>(`/sellers/${id}`),

  getByEmail: (email: string) =>
    api.get<Seller>(`/sellers/email/${email}`),

  getAuthUrl: (seller_email: string) =>
    api.post('/sellers/auth-url', null, { params: { seller_email } }),

  updateStatus: (id: string, is_active: boolean) =>
    api.put<MessageResponse>(`/sellers/${id}/status`, null, {
      params: { is_active },
    }),

  delete: (id: string) =>
    api.delete<MessageResponse>(`/sellers/${id}`),
}
