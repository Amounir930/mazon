export interface Product {
  id: string
  seller_id: string
  sku: string
  parent_sku?: string
  is_parent: boolean
  name: string
  category?: string
  brand?: string
  upc?: string
  ean?: string
  description?: string
  bullet_points: string[]
  keywords: string[]
  price: number
  compare_price?: number
  cost?: number
  quantity: number
  weight?: number
  dimensions?: { length: number; width: number; height: number; unit: string }
  images: string[]
  attributes: Record<string, unknown>
  status: 'draft' | 'queued' | 'processing' | 'published' | 'failed'
  optimized_data?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ProductCreate {
  sku: string
  parent_sku?: string
  is_parent?: boolean
  name: string
  category?: string
  brand?: string
  upc?: string
  ean?: string
  description?: string
  bullet_points?: string[]
  keywords?: string[]
  price: number
  compare_price?: number
  cost?: number
  quantity?: number
  weight?: number
  dimensions?: Record<string, unknown>
  images?: string[]
  attributes?: Record<string, unknown>
}

export interface Listing {
  id: string
  product_id: string
  seller_id: string
  feed_submission_id?: string
  status: 'queued' | 'processing' | 'submitted' | 'success' | 'failed'
  amazon_asin?: string
  amazon_url?: string
  error_message?: string
  queue_position?: number
  submitted_at?: string
  completed_at?: string
  created_at: string
}

export interface Seller {
  id: string
  email: string
  seller_id: string
  marketplace_id: string
  region: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

// Auth types
export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: Seller
}

export interface RegisterRequest {
  email: string
  password: string
  name?: string
}

export interface RegisterResponse {
  user: Seller
  message: string
}

export interface AuthUrlResponse {
  auth_url: string
  message: string
}

export interface MessageResponse {
  message: string
}

export interface ErrorResponse {
  error: string
  detail?: string
}
