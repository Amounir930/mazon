// Settings Hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'

// ==================== Settings Keys ====================

export const settingsKeys = {
  iamConfig: ['settings', 'iam-config'] as const,
  sessionInfo: ['settings', 'session-info'] as const,
  spCredentials: ['settings', 'sp-credentials'] as const,
}

// ==================== Settings Hooks ====================

export function useIAMConfig() {
  return useQuery({
    queryKey: settingsKeys.iamConfig,
    queryFn: async () => {
      const { data } = await settingsApi.getIAMConfig()
      return data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useSessionInfo() {
  return useQuery({
    queryKey: settingsKeys.sessionInfo,
    queryFn: async () => {
      const { data } = await settingsApi.getSessionInfo()
      return data
    },
    staleTime: 1000 * 30, // 30 seconds
    refetchInterval: 1000 * 30, // Refetch every 30 seconds
  })
}

export function useSPApiCredentials() {
  return useQuery({
    queryKey: settingsKeys.spCredentials,
    queryFn: async () => {
      const { data } = await settingsApi.getSPApiCredentials()
      return data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

export function useSaveSPApiCredentials() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (credentials: { client_id: string; client_secret: string; refresh_token: string; seller_id: string }) =>
      settingsApi.saveSPApiCredentials(credentials),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.spCredentials })
      queryClient.invalidateQueries({ queryKey: settingsKeys.sessionInfo })
      queryClient.invalidateQueries({ queryKey: ['auth', 'session'] })
      // Return the result so the component can use it
      return result
    },
  })
}
