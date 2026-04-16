/**
 * AI Product Generation — TypeScript Types
 * 
 * Base + Delta Pattern:
 * - base_product: shared data (same for all variants)
 * - variants: per-product differences (name, description, SKU)
 */

export interface PriceEstimate {
  min: number
  max: number
}

export interface BaseProductData {
  brand: string
  manufacturer: string
  product_type: string
  amazon_product_type?: string
  browse_node_id?: string
  price: number | null  // اختياري - AI يتركه null
  ean: string  // إجباري - 13 رقم
  upc: string
  bullet_points_ar: string[]
  bullet_points_en: string[]
  keywords: string[]
  material: string
  target_audience: string
  condition: string
  fulfillment_channel: string
  country_of_origin: string
  model_number: string
  included_components: string  // كلمة واحدة
  estimated_price_egp: PriceEstimate | null
}

export interface ProductVariant {
  variant_number: number
  name_ar: string
  name_en: string
  description_ar: string
  description_en: string
  suggested_sku: string
}

/** Full AI product generation response */
export interface AIProductGenerateResponse {
  base_product: BaseProductData
  variants: ProductVariant[]
  count: number
  warnings: string[]
  metadata: {
    model: string
    provider: string
    pattern: string
    tokens_saved: string
  }
}

/** Request to generate products */
export interface AIProductGenerateRequest {
  name: string
  specs: string
  copies: number
  brand?: string
}

/** Merged product for form submission */
export interface AIMergedProduct {
  // From base_product
  brand: string
  manufacturer: string
  product_type: string
  browse_node_id?: string
  price: number | null  // اختياري
  ean: string  // إجباري - 13 رقم
  upc: string
  bullet_points_ar: string[]
  bullet_points_en: string[]
  keywords: string[]
  material: string
  target_audience: string
  condition: string
  fulfillment_channel: string
  country_of_origin: string
  model_number: string
  included_components: string  // كلمة واحدة
  // From variant
  name_ar: string
  name_en: string
  description_ar: string
  description_en: string
  suggested_sku: string
  // From AI metadata
  ai_generated: true
  ai_score?: number
  seo_score?: number
}
