// ==================== AI Validation & Metadata Types ====================

export interface ValidationError {
  field: string
  message: string
  severity: 'error' | 'warning'
}

export interface AIGenerationMetadata {
  model_used: string
  tokens_used?: number
  fallback_used?: boolean
  contamination_checked?: boolean
  processing_time_ms?: number
}

// ==================== AI Types ====================

export interface AIMergedProduct {
  base_product: {
    brand: string
    manufacturer: string
    amazon_product_type: string
    browse_node_id: string
    product_type: string
    price: number | null
    ean: string
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
    included_components: string
    estimated_price_egp: number | null
    has_product_identifier?: boolean
    description_ar?: string
    description_en?: string
  }
  variants: Array<AIMergedVariant & {
    model_name?: string
  }>
  metadata?: AIGenerationMetadata
}

export interface AIMergedVariant {
  variant_number: number
  name_ar: string
  name_en: string
  description_ar: string
  description_en: string
  suggested_sku: string
}

// ✅ Fixed: Changed product_name → name, product_specs → specs
export interface AIGenerateProductRequest {
  name: string
  specs: string
  copies: number
  learned_fields?: string[]
  brand?: string
}

export interface AIGenerateProductResponse {
  success: boolean
  data?: AIMergedProduct
  error?: string
  message?: string
  validation_errors?: ValidationError[]
  warnings?: ValidationError[]
  fallback_used?: boolean
  metadata?: AIGenerationMetadata
}

export interface AILearnedFieldsResponse {
  learned_fields: string[]
  last_rejection_reasons?: string[]
  improvement_suggestions?: string[]
}

export interface AIImportAmazonRequest {
  asin: string
  product_type: string
  marketplace_id?: string
}

export interface AIImportAmazonResponse {
  success: boolean
  product?: AIMergedProduct
  error?: string
  message?: string
}
