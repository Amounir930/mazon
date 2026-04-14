import { useState } from 'react'
import { useSessionStatus, useLogout, useVerifySession, useDisconnectAmazon } from '@/api/hooks'
import { useIAMConfig, useSessionInfo } from '@/api/settings-hooks'
import {
  Shield, AlertTriangle, Loader2, CheckCircle, LogOut, RefreshCw, Mail,
  Key, Globe, Server, Eye, EyeOff, Lock, Settings2, Info, AlertCircle
} from 'lucide-react'
import AmazonLoginDirect from './AmazonLoginDirect'
import toast from 'react-hot-toast'

export default function UnifiedAuthPage() {
  const [showIAM, setShowIAM] = useState(false)
  const { data: session, isLoading: sessionLoading, refetch: refetchSession } = useSessionStatus()
  const { data: sessionInfo, isLoading: sessionInfoLoading } = useSessionInfo()
  const { data: iamConfig, isLoading: iamLoading } = useIAMConfig()
  const logoutMutation = useLogout()
  const verifyMutation = useVerifySession()
  const disconnectMutation = useDisconnectAmazon()

  const isConnected = session?.is_connected

  const handleLogout = async () => {
    await logoutMutation.mutateAsync()
    toast.success('تم تسجيل الخروج')
    refetchSession()
  }

  const handleDisconnect = async () => {
    if (session?.email) {
      await disconnectMutation.mutateAsync(session.email)
      toast.success('تم قطع الاتصال')
      refetchSession()
    }
  }

  const handleVerify = async () => {
    try {
      const result = await verifyMutation.mutateAsync()
      if (result.is_valid) {
        toast.success('الجلسة صالحة ✅')
      } else {
        toast.error('الجلسة انتهت - سجل الدخول مرة أخرى')
      }
    } catch {
      toast.error('فشل التحقق')
    }
    refetchSession()
  }

  const handleLoginSuccess = () => {
    refetchSession()
  }

  const isLoading = sessionLoading || sessionInfoLoading || iamLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-amazon-orange animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto" dir="rtl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Settings2 className="w-7 h-7 text-amazon-orange" />
          الإعدادات والاتصال
        </h1>
        <p className="text-gray-400 mt-1">إدارة اتصال Amazon وبيانات IAM</p>
      </div>

      {/* Connection Status Banner */}
      <ConnectionStatusCard
        isConnected={isConnected}
        session={session}
        sessionInfo={sessionInfo}
        onVerify={handleVerify}
        onDisconnect={handleDisconnect}
        onLogout={handleLogout}
        verifyLoading={verifyMutation.isPending}
        disconnectLoading={disconnectMutation.isPending}
        logoutLoading={logoutMutation.isPending}
      />

      {/* IAM Configuration Card */}
      <IAMConfigCard
        iamConfig={iamConfig}
        isLoading={iamLoading}
        expanded={showIAM}
        onToggle={() => setShowIAM(!showIAM)}
      />

      {/* Login Form - only show if not connected */}
      {!isConnected && <LoginForm onSuccess={handleLoginSuccess} />}
    </div>
  )
}

// ============================================================
// Connection Status Card
// ============================================================

interface ConnectionStatusProps {
  isConnected: boolean
  session: any
  sessionInfo: any
  onVerify: () => void
  onDisconnect: () => void
  onLogout: () => void
  verifyLoading: boolean
  disconnectLoading: boolean
  logoutLoading: boolean
}

function ConnectionStatusCard({
  isConnected, session, sessionInfo,
  onVerify, onDisconnect, onLogout,
  verifyLoading, disconnectLoading, logoutLoading
}: ConnectionStatusProps) {
  return isConnected ? (
    <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-500" />
          <div>
            <h3 className="text-green-400 font-bold">
              ✅ متصل ({session?.auth_method === 'browser' ? 'Browser' : 'SP-API'})
            </h3>
            <p className="text-xs text-gray-400">
              {session?.email || session?.seller_name || sessionInfo?.seller_name || sessionInfo?.email}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onVerify}
            disabled={verifyLoading}
            className="px-3 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-300 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${verifyLoading ? 'animate-spin' : ''}`} />
            تحقق
          </button>
          <button
            onClick={onDisconnect}
            disabled={disconnectLoading}
            className="px-3 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <LogOut className="w-4 h-4" />
            قطع
          </button>
          <button
            onClick={onLogout}
            disabled={logoutLoading}
            className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50"
          >
            <LogOut className="w-4 h-4" />
            خروج
          </button>
        </div>
      </div>

      {/* Session Details */}
      {sessionInfo && (
        <div className="mt-3 bg-gray-800/50 rounded-lg p-3 grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-gray-500">طريقة الاتصال:</span>
            <span className="text-gray-300 mr-2">{sessionInfo.auth_method || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">الدولة:</span>
            <span className="text-gray-300 mr-2">{sessionInfo.country_code?.toUpperCase() || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">الحالة:</span>
            <span className={sessionInfo.is_valid ? 'text-green-400 mr-2' : 'text-red-400 mr-2'}>
              {sessionInfo.is_valid ? 'صالحة ✅' : 'منتهية ❌'}
            </span>
          </div>
          <div>
            <span className="text-gray-500">آخر تحقق:</span>
            <span className="text-gray-300 mr-2">
              {sessionInfo.last_verified_at
                ? new Date(sessionInfo.last_verified_at).toLocaleString('ar-EG')
                : '-'}
            </span>
          </div>
        </div>
      )}
    </div>
  ) : (
    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
      <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
      <div>
        <h3 className="text-red-400 font-bold">غير متصل</h3>
        <p className="text-xs text-gray-400">سجل دخولك عبر Amazon للمتابعة</p>
      </div>
    </div>
  )
}

// ============================================================
// IAM Configuration Card
// ============================================================

interface IAMConfigCardProps {
  iamConfig: any
  isLoading: boolean
  expanded: boolean
  onToggle: () => void
}

function IAMConfigCard({ iamConfig, isLoading, expanded, onToggle }: IAMConfigCardProps) {
  if (isLoading) {
    return (
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6">
        <div className="flex items-center justify-center">
          <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
        </div>
      </div>
    )
  }

  if (!iamConfig) return null

  return (
    <div className="bg-[#12121a] rounded-xl border border-gray-800/50 overflow-hidden">
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Lock className="w-5 h-5 text-amazon-orange" />
          <h3 className="text-white font-bold">بيانات IAM (Amazon SP-API)</h3>
          {iamConfig.is_fully_configured ? (
            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">
              مكتملة ✅
            </span>
          ) : (
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-full">
              ناقصة ⚠️
            </span>
          )}
        </div>
        <Eye className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {/* Content */}
      {expanded && (
        <div className="px-6 pb-6 space-y-6 border-t border-gray-800/50 pt-4">
          {/* Full Config Status */}
          <div className={`p-4 rounded-lg flex items-start gap-3 ${
            iamConfig.is_fully_configured
              ? 'bg-green-500/10 border border-green-500/30'
              : 'bg-yellow-500/10 border border-yellow-500/30'
          }`}>
            <Info className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
              iamConfig.is_fully_configured ? 'text-green-400' : 'text-yellow-400'
            }`} />
            <div>
              <p className={`text-sm font-medium ${
                iamConfig.is_fully_configured ? 'text-green-300' : 'text-yellow-300'
              }`}>
                {iamConfig.is_fully_configured
                  ? 'جميع بيانات IAM مُكوّنة بشكل صحيح'
                  : 'بعض بيانات IAM مفقودة - تأكد من ملف .env'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                هذه البيانات ثابتة في ملف backend/.env ولا يمكن تعديلها من الواجهة
              </p>
            </div>
          </div>

          {/* AWS IAM Section */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-gray-300 flex items-center gap-2">
              <Server className="w-4 h-4" />
              AWS IAM Credentials
            </h4>
            <div className="bg-gray-800/50 rounded-lg p-4 space-y-3 text-sm">
              <ConfigRow label="AWS Access Key" value={iamConfig.aws_access_key_id} />
              <ConfigRow label="AWS Secret Key" value={iamConfig.aws_secret_key_masked} masked />
              <ConfigRow label="AWS Region" value={iamConfig.aws_region} />
              <ConfigRow label="AWS Role ARN" value={iamConfig.aws_role_arn} />
            </div>
          </div>

          {/* SP-API Section */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-gray-300 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              SP-API Credentials
            </h4>
            <div className="bg-gray-800/50 rounded-lg p-4 space-y-3 text-sm">
              <ConfigRow label="SP-API Client ID" value={iamConfig.sp_api_client_id} />
              <ConfigRow label="SP-API Client Secret" value={iamConfig.sp_api_client_secret_masked} masked />
              <ConfigRow
                label="Refresh Token"
                value={iamConfig.sp_api_refresh_token_configured ? 'مُكوّن ✅' : 'غير مُكوّن ❌'}
                status={iamConfig.sp_api_refresh_token_configured ? 'success' : 'error'}
              />
            </div>
          </div>

          {/* Marketplace Section */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-gray-300 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Marketplace Settings
            </h4>
            <div className="bg-gray-800/50 rounded-lg p-4 space-y-3 text-sm">
              <ConfigRow label="Seller ID" value={iamConfig.sp_api_seller_id} />
              <ConfigRow label="Marketplace ID" value={iamConfig.sp_api_marketplace_id} />
              <ConfigRow label="Country" value={iamConfig.sp_api_country?.toUpperCase()} />
            </div>
          </div>

          {/* Mock Mode Status */}
          <div className={`p-3 rounded-lg flex items-center gap-3 ${
            iamConfig.use_amazon_mock
              ? 'bg-yellow-500/10 border border-yellow-500/30'
              : 'bg-blue-500/10 border border-blue-500/30'
          }`}>
            <AlertCircle className={`w-4 h-4 flex-shrink-0 ${
              iamConfig.use_amazon_mock ? 'text-yellow-400' : 'text-blue-400'
            }`} />
            <p className={`text-xs ${
              iamConfig.use_amazon_mock ? 'text-yellow-300' : 'text-blue-300'
            }`}>
              {iamConfig.use_amazon_mock
                ? '⚠️ وضع Mock مُفعّل - يستخدم بيانات وهمية للاختبار'
                : '✅ وضع Production - يستخدم بيانات SP-API الحقيقية'}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================
// Config Row Component
// ============================================================

function ConfigRow({
  label,
  value,
  masked = false,
  status,
}: {
  label: string
  value: string | null
  masked?: boolean
  status?: 'success' | 'error'
}) {
  const [showValue, setShowValue] = useState(false)

  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-gray-400 text-xs">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`text-xs font-mono ${
          status === 'success' ? 'text-green-400' :
          status === 'error' ? 'text-red-400' :
          'text-gray-300'
        }`}>
          {value || '-'}
        </span>
        {masked && (
          <button
            onClick={() => setShowValue(!showValue)}
            className="text-gray-500 hover:text-gray-300 transition-colors"
            title={showValue ? 'إخفاء' : 'إظهار'}
          >
            {showValue ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
          </button>
        )}
      </div>
    </div>
  )
}

// ============================================================
// Login Form Component
// ============================================================

function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('')
  const [countryCode, setCountryCode] = useState('eg')

  return (
    <div className="space-y-6">
      {/* Important notice */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 flex items-start gap-3">
        <Shield className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="text-blue-300 font-bold text-sm mb-1">ℹ️ تسجيل الدخول المباشر</h3>
          <p className="text-blue-300/70 text-xs leading-relaxed">
            سيتم فتح صفحة Amazon Seller Central في نافذة جديدة.
            <br />
            أدخل بياناتك مباشرة وسيتم الاتصال تلقائياً.
          </p>
        </div>
      </div>

      {/* Email & Country Input */}
      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6 space-y-4">
        <h3 className="text-white font-bold flex items-center gap-2">
          <Mail className="w-5 h-5 text-amazon-orange" />
          بيانات الحساب
        </h3>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            البريد الإلكتروني
          </label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="seller@example.com"
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-amazon-orange outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            الدولة
          </label>
          <select
            value={countryCode}
            onChange={e => setCountryCode(e.target.value)}
            className="w-full bg-[#0a0a0f] border border-gray-700 rounded-lg px-4 py-3 text-white focus:border-amazon-orange outline-none"
          >
            <option value="eg">🇪🇬 مصر</option>
            <option value="sa">🇸🇦 السعودية</option>
            <option value="ae">🇦🇪 الإمارات</option>
            <option value="uk">🇬🇧 المملكة المتحدة</option>
            <option value="us">🇺 الولايات المتحدة</option>
          </select>
        </div>

        {/* Amazon Login Direct - Backend opens PyWebView window */}
        <AmazonLoginDirect
          country_code={countryCode}
          onSuccess={onSuccess}
        />
      </div>
    </div>
  )
}
