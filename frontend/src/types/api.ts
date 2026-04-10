// ==================== Amazon Connect ====================

export interface AmazonConnectRequest {
  lwa_client_id: string
  lwa_client_secret: string
  lwa_refresh_token: string
  amazon_seller_id: string
  display_name?: string
  marketplace_id?: string
}

export interface AmazonConnectResponse {
  seller_id: string | null
  amazon_seller_id: string | null
  is_connected: boolean
  display_name: string | null
  marketplace_id: string | null
  last_sync_at: string | null
  message: string
}

export interface AmazonVerifyResponse {
  is_connected: boolean
  message: string
}

// ==================== Product ====================

export interface Product {
  id: string
  sku: string
  name: string
  name_ar?: string
  name_en?: string
  category?: string
  brand?: string
  price: number
  compare_price?: number
  cost?: number
  quantity: number
  weight?: number
  description?: string
  description_ar?: string
  description_en?: string
  bullet_points: string[]
  bullet_points_ar?: string[]
  bullet_points_en?: string[]
  keywords: string[]
  dimensions?: Record<string, unknown>
  images: string[]
  attributes: Record<string, unknown>
  status: 'draft' | 'queued' | 'processing' | 'published' | 'failed'
  created_at: string
  updated_at: string
}

export interface ProductCreate {
  sku: string
  name: string
  name_ar?: string
  name_en?: string
  category?: string
  brand?: string
  price: number
  compare_price?: number
  cost?: number
  quantity?: number
  weight?: number
  description?: string
  description_ar?: string
  description_en?: string
  bullet_points?: string[]
  bullet_points_ar?: string[]
  bullet_points_en?: string[]
  keywords?: string[]
  dimensions?: Record<string, unknown>
  images?: string[]
  attributes?: Record<string, unknown>
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

// ==================== Listing ====================

export interface Listing {
  id: string
  product_id: string
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

// ==================== Task ====================

export interface TaskStatus {
  status: 'queued' | 'running' | 'completed' | 'failed'
  result?: unknown
  error?: string
  started_at?: string
  completed_at?: string
}

// ==================== Generic ====================

export interface MessageResponse {
  message: string
}

export interface ErrorResponse {
  error: string
  detail?: string
}
