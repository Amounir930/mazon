// API Base URL
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Endpoints
export const ENDPOINTS = {
  // Auth
  AUTH_URL: `${API_BASE_URL}/sellers/auth-url`,
  OAUTH_CALLBACK: `${API_BASE_URL}/sellers/oauth/callback`,

  // Products
  PRODUCTS: `${API_BASE_URL}/products`,
  PRODUCT: (id: string) => `${API_BASE_URL}/products/${id}`,

  // Listings
  LISTINGS: `${API_BASE_URL}/listings`,
  LISTING_SUBMIT: `${API_BASE_URL}/listings/submit`,
  LISTING: (id: string) => `${API_BASE_URL}/listings/${id}`,

  // Feeds
  FEED_STATUS: (id: string) => `${API_BASE_URL}/feeds/${id}/status`,

  // Sellers
  SELLERS: `${API_BASE_URL}/sellers`,
  SELLER_REGISTER: `${API_BASE_URL}/sellers/register`,
  SELLER: (id: string) => `${API_BASE_URL}/sellers/${id}`,
} as const

// Health check
export const HEALTH_URL = `${API_BASE_URL}/health`.replace('/api/v1', '')
