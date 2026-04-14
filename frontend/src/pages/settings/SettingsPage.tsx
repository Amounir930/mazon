import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useSessionStatus, useLogout, useVerifySession } from '@/api/hooks'
import { useIAMConfig, useSessionInfo, useSPApiCredentials, useSaveSPApiCredentials } from '@/api/settings-hooks'
import {
  Loader2, CheckCircle, LogOut, RefreshCw,
  Globe, Server, Eye, EyeOff, Settings2, Save, AlertTriangle, Edit
} from 'lucide-react'
import { NeonButton } from '@/components/common'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { t } = useTranslation()
  const [showIAM, setShowIAM] = useState(false)
  const { data: session, isLoading: sessionLoading, refetch: refetchSession } = useSessionStatus()
  const { data: iamConfig, isLoading: iamLoading } = useIAMConfig()
  const { data: spCredentials, isLoading: spLoading, refetch: refetchSP } = useSPApiCredentials()
  const saveMutation = useSaveSPApiCredentials()

  const [spClientId, setSpClientId] = useState('')
  const [spClientSecret, setSpClientSecret] = useState('')
  const [spRefreshToken, setSpRefreshToken] = useState('')
  const [spSellerId, setSpSellerId] = useState('')
  const [showSecret, setShowSecret] = useState(false)
  const [editingSecret, setEditingSecret] = useState(false)

  useEffect(() => {
    if (spCredentials) {
      setSpClientId(spCredentials.client_id || '')
      setSpClientSecret(spCredentials.client_secret || '')
      setSpRefreshToken(spCredentials.refresh_token || '')
      setSpSellerId(spCredentials.seller_id || '')
    }
  }, [spCredentials])

  const handleSaveSP = async () => {
    if (!spSellerId.trim()) { toast.error(t('settings.requiredFields.sellerId')); return }
    if (!spClientId.trim()) { toast.error(t('settings.requiredFields.clientId')); return }
    if (!spRefreshToken.trim()) { toast.error(t('settings.requiredFields.refreshToken')); return }

    const secretToSend = editingSecret ? spClientSecret : (spCredentials?.client_secret || '')

    try {
      const result = await saveMutation.mutateAsync({
        client_id: spClientId,
        client_secret: secretToSend,
        refresh_token: spRefreshToken,
        seller_id: spSellerId,
      })

      if (result.data.is_connected) {
        toast.success(result.data.message)
      } else {
        toast.error(result.data.message || 'فشل الاتصال بـ Amazon', { duration: 8000 })
      }

      refetchSP()
      refetchSession()
    } catch (e: any) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'فشل الحفظ'
      toast.error(errorMsg, { duration: 10000 })
    }
  }

  const handleVerify = async () => {
    try {
      const result = await verifyMutation.mutateAsync()

      // useVerifyConnection returns data directly (not Axios response)
      if (result.is_valid || result.is_connected) {
        toast.success(t('settings.verifySuccess'))
      } else {
        toast.error(t('settings.verifyError'))
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || t('settings.verifyError'))
    }
    refetchSession()
  }

  const handleLogout = async () => {
    await logoutMutation.mutateAsync()
    toast.success(t('settings.logoutSuccess'))
    refetchSession()
  }

  const isLoading = sessionLoading || iamLoading || spLoading
  const verifyMutation = useVerifySession()
  const logoutMutation = useLogout()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto" dir="rtl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <Settings2 className="w-7 h-7 text-amazon-orange" />
          {t('settings.title')}
        </h1>
        <p className="text-text-secondary mt-1">{t('settings.subtitle')}</p>
      </div>

      {/* Connection Status */}
      <ConnectionStatus
        session={session}
        onVerify={handleVerify}
        onLogout={handleLogout}
        verifyLoading={verifyMutation.isPending}
        logoutLoading={logoutMutation.isPending}
        t={t}
      />

      {/* IAM Configuration */}
      <IAMConfigCard
        iamConfig={iamConfig}
        expanded={showIAM}
        onToggle={() => setShowIAM(!showIAM)}
        t={t}
      />

      {/* SP-API Credentials */}
      <SPApiCard
        isConnected={session?.is_connected}
        sellerId={spSellerId}
        onSellerIdChange={setSpSellerId}
        clientId={spClientId}
        onClientIdChange={setSpClientId}
        clientSecret={spClientSecret}
        onClientSecretChange={setSpClientSecret}
        showSecret={showSecret}
        onToggleSecret={() => setShowSecret(!showSecret)}
        refreshToken={spRefreshToken}
        onRefreshTokenChange={setSpRefreshToken}
        editingSecret={editingSecret}
        onToggleEditSecret={() => {
          setEditingSecret(!editingSecret)
          if (editingSecret) refetchSP()
        }}
        onSave={handleSaveSP}
        saving={saveMutation.isPending}
        t={t}
      />
    </div>
  )
}

// ============================================================
// Connection Status - Dark Theme + i18n
// ============================================================

function ConnectionStatus({ session, onVerify, onLogout, verifyLoading, logoutLoading, t }: any) {
  const isConnected = session?.is_connected

  return isConnected ? (
    <div className="neon-card neon-card--accent neon-card--green">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-neon-cyan/10 border border-neon-cyan/20 flex items-center justify-center">
            <CheckCircle className="w-6 h-6 text-neon-cyan" />
          </div>
          <div>
            <h3 className="text-text-primary font-bold">{t('settings.connected')}</h3>
            <p className="text-xs text-text-secondary">
              {session?.seller_name || session?.email || t('settings.connectedDesc')}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={onVerify} disabled={verifyLoading}
            className="neon-btn neon-btn--success neon-btn--sm">
            <RefreshCw className={`w-4 h-4 ${verifyLoading ? 'animate-spin' : ''}`} /> {t('settings.verify')}
          </button>
          <button onClick={onLogout} disabled={logoutLoading}
            className="neon-btn neon-btn--danger neon-btn--sm">
            <LogOut className="w-4 h-4" /> {t('settings.logout')}
          </button>
        </div>
      </div>
    </div>
  ) : (
    <div className="neon-card neon-card--accent neon-card--red">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-neon-red/10 border border-neon-red/20 flex items-center justify-center flex-shrink-0">
          <AlertTriangle className="w-5 h-5 text-neon-red" />
        </div>
        <div>
          <h3 className="text-text-primary font-bold">{t('settings.disconnected')}</h3>
          <p className="text-xs text-text-secondary">{t('settings.disconnectedDesc')}</p>
        </div>
      </div>
    </div>
  )
}

// ============================================================
// IAM Config Card - Dark Theme + i18n
// ============================================================

function IAMConfigCard({ iamConfig, expanded, onToggle, t }: any) {
  if (!iamConfig) return null

  return (
    <div className="neon-card">
      <button onClick={onToggle}
        className="w-full flex items-center justify-between hover:bg-bg-hover/50 transition-colors -m-6 p-6 rounded-t-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-bg-elevated/50 border border-border-subtle flex items-center justify-center">
            <Server className="w-5 h-5 text-text-secondary" />
          </div>
          <h3 className="text-text-primary font-bold">{t('settings.iamTitle')}</h3>
          {iamConfig.is_fully_configured ? (
            <span className="text-xs bg-neon-cyan/10 text-neon-cyan px-3 py-1 rounded-full border border-neon-cyan/20">{t('settings.iamComplete')}</span>
          ) : (
            <span className="text-xs bg-neon-yellow/10 text-neon-yellow px-3 py-1 rounded-full border border-neon-yellow/20">{t('settings.iamIncomplete')}</span>
          )}
        </div>
        <span className="text-xs text-text-muted">{t('settings.iamReadOnly')}</span>
      </button>

      {expanded && (
        <div className="space-y-4 border-t border-border-subtle pt-4">
          <div className={`p-3 rounded-lg text-xs ${iamConfig.is_fully_configured
              ? 'bg-neon-cyan/5 text-neon-cyan border border-neon-cyan/20'
              : 'bg-neon-yellow/5 text-neon-yellow border border-neon-yellow/20'
            }`}>
            {iamConfig.is_fully_configured
              ? t('settings.iamAllConfigured')
              : t('settings.iamMissing')}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-text-muted mb-2">{t('settings.awsIam')}</h4>
            <div className="space-y-1.5">
              <ConfigRow label={t('settings.accessKey')} value={iamConfig.aws_access_key_id} />
              <ConfigRow label={t('settings.region')} value={iamConfig.aws_region} />
              <ConfigRow label={t('settings.roleArn')} value={iamConfig.aws_role_arn} />
            </div>
          </div>
          <div>
            <h4 className="text-xs font-semibold text-text-muted mb-2">{t('settings.marketplace')}</h4>
            <div className="space-y-1.5">
              <ConfigRow label={t('settings.sellerId')} value={iamConfig.sp_api_seller_id} />
              <ConfigRow label={t('settings.marketplaceId')} value={iamConfig.sp_api_marketplace_id} />
              <ConfigRow label={t('settings.country')} value={iamConfig.sp_api_country?.toUpperCase()} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================
// SP-API Credentials Card - Dark Theme + Neon Inputs + i18n
// ============================================================

function SPApiCard({
  isConnected,
  sellerId, onSellerIdChange,
  clientId, onClientIdChange,
  clientSecret, onClientSecretChange, showSecret, onToggleSecret,
  refreshToken, onRefreshTokenChange,
  editingSecret, onToggleEditSecret,
  onSave, saving,
  t,
}: any) {
  const isSecretMasked = clientSecret?.includes('•')
  const isLocked = isConnected // مقفول لما يكون متصل

  return (
    <div className={`neon-card ${isLocked ? 'neon-card--locked' : 'neon-card--accent neon-card--orange'}`}>
      <div className="px-6 py-4 border-b border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isLocked ? 'bg-gray-500/20 border-gray-500/30' : 'bg-gradient-to-br from-amazon-orange/20 to-amazon-light/10 border border-amazon-orange/30'}`}>
            <Globe className={`w-5 h-5 ${isLocked ? 'text-gray-500' : 'text-amazon-orange'}`} />
          </div>
          <div>
            <h3 className="text-text-primary font-bold">{t('settings.spApiTitle')}</h3>
            <p className="text-xs text-text-muted">{t('settings.spApiDesc')}</p>
          </div>
        </div>
        {isLocked && (
          <span className="text-xs bg-green-500/20 text-green-400 px-3 py-1 rounded-full flex items-center gap-1">
            🔒 {t('settings.locked')}
          </span>
        )}
      </div>

      <div className={`px-6 pb-6 pt-4 space-y-4 ${isLocked ? 'opacity-50 pointer-events-none' : ''}`}>
        {/* Seller ID */}
        <div className="neon-input-group">
          <label className="neon-label">{t('settings.sellerId')}</label>
          <input type="text" value={sellerId} onChange={e => onSellerIdChange(e.target.value)}
            placeholder="A1DSHARRBRWYZW"
            className="neon-input neon-input--orange"
            dir="ltr" />
          <span className="neon-helper">{t('settings.spApiSellerIdDesc')}</span>
        </div>

        {/* Client ID */}
        <div className="neon-input-group">
          <label className="neon-label">{t('settings.spApiClientId')}</label>
          <input type="text" value={clientId} onChange={e => onClientIdChange(e.target.value)}
            placeholder="amzn1.application-oa2-client.xxxxxx"
            className="neon-input"
            dir="ltr" />
          <span className="neon-helper">{t('settings.spApiClientIdDesc')}</span>
        </div>

        {/* Client Secret */}
        <div className="neon-input-group">
          <div className="flex items-center justify-between mb-1">
            <label className="neon-label">{t('settings.spApiClientSecret')}</label>
            {isSecretMasked && !editingSecret && (
              <button onClick={onToggleEditSecret}
                className="text-xs text-amazon-orange hover:text-amazon-light flex items-center gap-1 transition-colors">
                <Edit className="w-3 h-3" /> {t('settings.change')}
              </button>
            )}
          </div>
          <div className="relative">
            <input
              type={showSecret ? 'text' : 'password'}
              value={clientSecret}
              onChange={e => onClientSecretChange(e.target.value)}
              placeholder={isSecretMasked && !editingSecret ? '••••••••' : 'amzn1.oa2-cs.v1.xxxxxx'}
              className="neon-input pr-10"
              dir="ltr"
              readOnly={isSecretMasked && !editingSecret}
            />
            {!editingSecret && (
              <button onClick={onToggleSecret}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                type="button">
                {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            )}
          </div>
          {isSecretMasked && !editingSecret && (
            <span className="neon-helper">{t('settings.secretSaved')}</span>
          )}
        </div>

        {/* Refresh Token */}
        <div className="neon-input-group">
          <label className="neon-label">{t('settings.spApiRefreshToken')}</label>
          <textarea value={refreshToken} onChange={e => onRefreshTokenChange(e.target.value)}
            placeholder="Atzr|IwEB..." rows={2}
            className="neon-input neon-textarea resize-none"
            dir="ltr" />
          <span className="neon-helper">{t('settings.spApiRefreshTokenDesc')}</span>
        </div>

        {/* Save Button */}
        <NeonButton variant="amazon" fullWidth isLoading={saving} onClick={onSave}>
          <Save className="w-5 h-5" /> {t('settings.saveSPApi')}
        </NeonButton>
      </div>
    </div>
  )
}

// ============================================================
// Config Row - Dark Theme
// ============================================================

function ConfigRow({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex items-center justify-between gap-4 text-xs px-3 py-2 rounded-lg bg-bg-tertiary/50">
      <span className="text-text-muted">{label}</span>
      <span className="font-mono text-text-secondary" dir="ltr">{value || '-'}</span>
    </div>
  )
}
