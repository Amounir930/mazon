import api from '@/lib/axios'
import type {
  AIMergedProduct,
  AIGenerateProductRequest,
  AIGenerateProductResponse,
  AILearnedFieldsResponse,
  AIImportAmazonRequest,
  AIImportAmazonResponse,
  ValidationError,
} from '@/types/ai'

// ==================== AI API ====================

export const aiApi = {
  // Generate product using AI
  generateProduct: async (data: AIGenerateProductRequest) => {
    try {
      // ✅ Normalize field names for backward compatibility
      // Convert any legacy format to current backend format
      const backendData = {
        name: (data as any).product_name || data.name,
        specs: (data as any).product_specs || data.specs,
        copies: data.copies,
        learned_fields: data.learned_fields,
        brand: data.brand,
      }

      const response = await api.post<AIGenerateProductResponse>(
        '/ai/generate-product',
        backendData
      )

      // ✅ Auto-handle warnings
      if (response.data.warnings?.length) {
        console.warn('AI Generation warnings:', response.data.warnings)
      }

      return response
    } catch (error: any) {
      // ✅ Enhanced error handling for validation errors
      if (error.response?.data?.validation_errors) {
        const errors = error.response.data.validation_errors as ValidationError[]
        console.error('Validation errors:', errors)
      }
      throw error
    }
  },

  // Get learned fields that failed validation before
  getLearnedFields: (productId: string) =>
    api.get<AILearnedFieldsResponse>(`/ai/learned-fields/${productId}`),

  // Import product from Amazon using AI
  importFromAmazon: (data: AIImportAmazonRequest) =>
    api.post<AIImportAmazonResponse>('/ai/import-from-amazon', data),
}
