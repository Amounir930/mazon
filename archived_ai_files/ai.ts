/**
 * AI Product Generation — API Client
 */
import axiosInstance from '@/lib/axios'
import type {
  AIProductGenerateRequest,
  AIProductGenerateResponse,
} from '@/types/ai'

export const aiApi = {
  /**
   * Generate N product variants using Qwen AI
   * POST /api/v1/ai/generate-product
   */
  async generateProduct(
    data: AIProductGenerateRequest
  ): Promise<AIProductGenerateResponse> {
    const response = await axiosInstance.post('/ai/generate-product', data)
    return response.data
  },
}
