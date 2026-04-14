// Settings API
import api from '@/lib/axios'

export interface IAMConfigResponse {
  aws_access_key_id: string | null
  aws_secret_key_masked: string | null
  aws_region: string | null
  aws_role_arn: string | null
  sp_api_client_id: string | null
  sp_api_client_secret_masked: string | null
  sp_api_refresh_token_configured: boolean
  sp_api_seller_id: string | null
  sp_api_marketplace_id: string | null
  sp_api_country: string | null
  use_amazon_mock: boolean
  is_fully_configured: boolean
}

export interface SessionInfoResponse {
  is_connected: boolean
  auth_method: string | null
  seller_name: string | null
  email: string | null
  country_code: string | null
  is_valid: boolean
  last_verified_at: string | null
}

export interface SPApiCredentialsResponse {
  seller_id: string
  client_id: string
  client_secret: string  // Masked for security
  refresh_token: string
}

export interface SaveSPApiCredentialsRequest {
  client_id: string
  client_secret: string
  refresh_token: string
  seller_id: string
}

export interface SaveSPApiCredentialsResponse {
  message: string
  is_connected: boolean
  verification?: {
    is_valid: boolean
    message?: string
    error?: string
    checked_at: string
  }
}

export const settingsApi = {
  getIAMConfig: () =>
    api.get<IAMConfigResponse>('/settings/iam-config'),

  getSessionInfo: () =>
    api.get<SessionInfoResponse>('/settings/session-info'),

  getSPApiCredentials: () =>
    api.get<SPApiCredentialsResponse>('/settings/sp-credentials'),

  saveSPApiCredentials: (data: SaveSPApiCredentialsRequest) =>
    api.post<SaveSPApiCredentialsResponse>('/settings/sp-credentials', data),
}
