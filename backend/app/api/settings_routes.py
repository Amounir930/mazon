"""
Settings API Routes
عرض بيانات الإعدادات (IAM Config, Session Info, SP-API Credentials)
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os
from app.models.session import Session as SessionModel
from app.database import SessionLocal
from loguru import logger
from dotenv import load_dotenv

router = APIRouter(prefix="/settings", tags=["settings"])


# ============================================================
# Request/Response Schemas
# ============================================================

class IAMConfigResponse(BaseModel):
    """IAM Configuration (with masked secrets) - READ ONLY"""
    aws_access_key_id: Optional[str]
    aws_secret_key_masked: Optional[str]
    aws_region: Optional[str]
    aws_role_arn: Optional[str]
    sp_api_client_id: Optional[str]
    sp_api_client_secret_masked: Optional[str]
    sp_api_refresh_token_configured: bool
    sp_api_seller_id: Optional[str]
    sp_api_marketplace_id: Optional[str]
    sp_api_country: Optional[str]
    use_amazon_mock: bool
    is_fully_configured: bool


class SessionInfoResponse(BaseModel):
    """Current Session Information"""
    is_connected: bool
    auth_method: Optional[str] = None
    seller_name: Optional[str] = None
    email: Optional[str] = None
    country_code: Optional[str] = None
    is_valid: bool = False
    last_verified_at: Optional[str] = None


class SPApiCredentialsResponse(BaseModel):
    """SP-API Credentials (editable) - Client Secret is masked for security"""
    seller_id: str = ""
    client_id: str = ""
    client_secret: str = ""  # Masked for security
    refresh_token: str = ""


class SaveSPApiCredentialsRequest(BaseModel):
    """Request to save SP-API credentials"""
    client_id: str
    client_secret: str
    refresh_token: str
    seller_id: str


# ============================================================
# Helper Functions
# ============================================================

def mask_secret(secret: Optional[str], visible_chars: int = 4) -> Optional[str]:
    """Mask a secret string, showing only the first few characters"""
    if not secret:
        return None
    if len(secret) <= visible_chars:
        return "***"
    return secret[:visible_chars] + "•" * (len(secret) - visible_chars)


def get_iam_config() -> IAMConfigResponse:
    """Get IAM configuration with masked secrets (READ ONLY from .env file)"""
    # Read directly from .env file to ensure we get latest values
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key.strip()] = value.strip()
    
    aws_access_key = env_vars.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = env_vars.get("AWS_SECRET_ACCESS_KEY")
    aws_region = env_vars.get("AWS_REGION")
    aws_role_arn = env_vars.get("AWS_SELLER_ROLE_ARN")

    sp_api_client_id = env_vars.get("SP_API_CLIENT_ID")
    sp_api_client_secret = env_vars.get("SP_API_CLIENT_SECRET")
    sp_api_refresh_token = env_vars.get("SP_API_REFRESH_TOKEN")

    seller_id = env_vars.get("SP_API_SELLER_ID")
    marketplace_id = env_vars.get("SP_API_MARKETPLACE_ID")
    country = env_vars.get("SP_API_COUNTRY")

    use_mock = env_vars.get("USE_AMAZON_MOCK", "False").lower() == "true"

    has_aws = all([aws_access_key, aws_secret_key, aws_region])
    has_sp_api = all([sp_api_client_id, sp_api_refresh_token])  # Client Secret optional
    has_seller = all([seller_id, marketplace_id])
    is_fully_configured = has_aws and has_sp_api and has_seller

    return IAMConfigResponse(
        aws_access_key_id=mask_secret(aws_access_key) if aws_access_key else None,
        aws_secret_key_masked=mask_secret(aws_secret_key) if aws_secret_key else None,
        aws_region=aws_region,
        aws_role_arn=aws_role_arn,
        sp_api_client_id=mask_secret(sp_api_client_id) if sp_api_client_id else None,
        sp_api_client_secret_masked=mask_secret(sp_api_client_secret) if sp_api_client_secret else None,
        sp_api_refresh_token_configured=bool(sp_api_refresh_token),
        sp_api_seller_id=seller_id,
        sp_api_marketplace_id=marketplace_id,
        sp_api_country=country,
        use_amazon_mock=use_mock,
        is_fully_configured=is_fully_configured,
    )


def _get_sp_credentials() -> SPApiCredentialsResponse:
    """Get SP-API credentials for editing (from .env file directly)"""
    import os
    
    # Read directly from .env file to ensure we get latest values
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key.strip()] = value.strip()
    
    seller_id = env_vars.get("SP_API_SELLER_ID", "")
    client_id = env_vars.get("SP_API_CLIENT_ID", "")
    client_secret = env_vars.get("SP_API_CLIENT_SECRET", "")
    refresh_token = env_vars.get("SP_API_REFRESH_TOKEN", "")

    return SPApiCredentialsResponse(
        seller_id=seller_id,
        client_id=client_id,
        client_secret=mask_secret(client_secret) if client_secret else "",  # Masked for security
        refresh_token=refresh_token,
    )


def _save_sp_credentials(data: SaveSPApiCredentialsRequest):
    """Save SP-API credentials to .env file"""
    import os
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')

    # Read existing .env
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key.strip()] = value.strip()

    # Update SP-API credentials
    env_vars['SP_API_SELLER_ID'] = data.seller_id
    env_vars['SP_API_CLIENT_ID'] = data.client_id
    # Only update client_secret if it's provided and not masked (doesn't contain •)
    if data.client_secret and '•' not in data.client_secret:
        env_vars['SP_API_CLIENT_SECRET'] = data.client_secret
    env_vars['SP_API_REFRESH_TOKEN'] = data.refresh_token

    # Write back to .env - preserve format
    with open(env_path, 'w', encoding='utf-8') as f:
        # First write known keys in order
        ordered_keys = [
            'APP_NAME', 'DEBUG', 'API_V1_PREFIX',
            'SP_API_CLIENT_ID', 'SP_API_CLIENT_SECRET', 'SP_API_REFRESH_TOKEN',
            'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 'AWS_SELLER_ROLE_ARN',
            'SP_API_SELLER_ID', 'SP_API_MARKETPLACE_ID', 'SP_API_COUNTRY',
            'USE_AMAZON_MOCK', 'LOG_LEVEL', 'LOG_ROTATION', 'LOG_RETENTION', 'QWEN_API_KEY'
        ]
        
        written_keys = set()
        for key in ordered_keys:
            if key in env_vars:
                f.write(f'{key}={env_vars[key]}\n')
                written_keys.add(key)
        
        # Write any remaining keys
        for key, value in env_vars.items():
            if key not in written_keys:
                f.write(f'{key}={value}\n')

    # Force reload environment variables
    load_dotenv(env_path, override=True)
    
    logger.info(f"SP-API credentials saved. Seller: {data.seller_id}")


# ============================================================
# Routes
# ============================================================

@router.get("/iam-config", response_model=IAMConfigResponse)
async def get_settings_iam_config():
    """
    عرض بيانات IAM Configuration (READ ONLY من .env)
    """
    return get_iam_config()


@router.get("/session-info", response_model=SessionInfoResponse)
async def get_session_info():
    """
    عرض معلومات الجلسة الحالية
    يشيك على:
    1. Session في قاعدة البيانات (Browser login)
    2. SP-API credentials في .env (Direct login)
    """
    try:
        db = SessionLocal()
        try:
            # أولاً: شوف لو فيه session في DB
            session = db.query(SessionModel).filter(
                SessionModel.is_active == True,  # noqa: E712
                SessionModel.is_valid == True,  # noqa: E712
            ).first()

            if session:
                return SessionInfoResponse(
                    is_connected=True,
                    auth_method=session.auth_method,
                    seller_name=session.seller_name,
                    email=session.email,
                    country_code=session.country_code,
                    is_valid=session.is_valid,
                    last_verified_at=session.last_verified_at.isoformat() if session.last_verified_at else None,
                )
        finally:
            db.close()

        # ثانياً: لو مفيش session، شوف لو SP-API credentials موجودة في .env
        # Read directly from .env file to ensure we get latest values
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        env_vars[key.strip()] = value.strip()
        
        seller_id = env_vars.get("SP_API_SELLER_ID")
        client_id = env_vars.get("SP_API_CLIENT_ID")
        refresh_token = env_vars.get("SP_API_REFRESH_TOKEN")
        country = env_vars.get("SP_API_COUNTRY", "eg")

        # Check if we have the essential credentials
        has_credentials = all([seller_id, client_id, refresh_token])

        if has_credentials:
            return SessionInfoResponse(
                is_connected=True,
                auth_method="sp_api",
                seller_name=seller_id,
                email=None,
                country_code=country,
                is_valid=True,
                last_verified_at=None,
            )

        # لا session ولا credentials
        return SessionInfoResponse(is_connected=False)

    except Exception as e:
        logger.error(f"Session info error: {e}", exc_info=True)
        return SessionInfoResponse(is_connected=False)


@router.get("/sp-credentials", response_model=SPApiCredentialsResponse)
async def get_sp_credentials():
    """
    عرض بيانات SP-API Credentials (قابلة للتعديل)
    """
    return _get_sp_credentials()


@router.post("/sp-credentials")
async def save_sp_credentials(data: SaveSPApiCredentialsRequest):
    """
    حفظ بيانات SP-API Credentials في ملف .env
    + التحقق من الاتصال بـ Amazon
    """
    try:
        logger.info(f"📝 Saving SP-API credentials for seller: {data.seller_id}")
        
        # 1. حفظ البيانات
        _save_sp_credentials(data)
        logger.info("✅ Credentials saved to .env file")

        # 2. التحقق من الاتصال بـ Amazon
        logger.info("🔍 Verifying connection with Amazon SP-API...")
        verification_result = _verify_sp_api_connection()

        if verification_result["is_valid"]:
            logger.info("✅ Amazon SP-API connection verified successfully!")
            return {
                "message": "✅ تم حفظ بيانات SP-API بنجاح - الاتصال بـ Amazon صالح!",
                "is_connected": True,
                "verification": verification_result,
            }
        else:
            logger.warning(f"⚠️ Amazon SP-API connection failed: {verification_result.get('error')}")
            return {
                "message": f"⚠️ تم حفظ البيانات لكن الاتصال بـ Amazon فشل: {verification_result.get('error', 'خطأ غير معروف')}",
                "is_connected": False,
                "verification": verification_result,
            }
    except Exception as e:
        logger.error(f"Failed to save SP-API credentials: {e}", exc_info=True)
        raise Exception(f"فشل الحفظ: {str(e)}")


def _verify_sp_api_connection() -> dict:
    """
    التحقق من اتصال SP-API بـ Amazon
    """
    try:
        import os
        from datetime import datetime
        
        # قراءة البيانات من .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        env_vars[key.strip()] = value.strip()
        
        # التحقق من وجود البيانات الأساسية
        client_id = env_vars.get("SP_API_CLIENT_ID", "")
        refresh_token = env_vars.get("SP_API_REFRESH_TOKEN", "")
        aws_access_key = env_vars.get("AWS_ACCESS_KEY_ID", "")
        aws_secret_key = env_vars.get("AWS_SECRET_ACCESS_KEY", "")
        country = env_vars.get("SP_API_COUNTRY", "eg")
        
        logger.info(f" Checking credentials: Client ID={client_id[:20]}..., Refresh Token={refresh_token[:20]}..., AWS Key={aws_access_key[:10]}...")
        
        if not all([client_id, refresh_token, aws_access_key, aws_secret_key]):
            logger.warning("❌ Incomplete SP-API credentials")
            return {
                "is_valid": False,
                "error": "بيانات SP-API غير مكتملة",
                "checked_at": datetime.now().isoformat(),
            }
        
        # محاولة الاتصال بـ Amazon SP-API
        logger.info("🔍 Attempting to connect to Amazon SP-API...")
        
        # استخدام SPAPIClient للتحقق
        from app.services.sp_api_client import SPAPIClient
        
        try:
            client = SPAPIClient(country_code=country)
            
            # محاولة الحصول على access token
            logger.info("🔄 Requesting access token from LWA...")
            access_token = client._get_access_token()
            
            if access_token:
                logger.info(f"✅ Successfully obtained access token: {access_token[:20]}...")
                return {
                    "is_valid": True,
                    "message": "الاتصال بـ Amazon صالح",
                    "checked_at": datetime.now().isoformat(),
                }
            else:
                logger.warning("❌ Failed to get access token (returned None)")
                return {
                    "is_valid": False,
                    "error": "فشل في الحصول على access token",
                    "checked_at": datetime.now().isoformat(),
                }
        except Exception as sp_error:
            error_msg = str(sp_error)
            logger.error(f"❌ SP-API connection failed: {error_msg}")
            
            # Provide user-friendly error messages
            if "LWA Error 400" in error_msg:
                if "invalid_client" in error_msg.lower():
                    user_friendly_error = "❌ Client ID أو Client Secret غير صحيح - راجع البيانات من Amazon Developer Console"
                elif "invalid_grant" in error_msg.lower():
                    user_friendly_error = "❌ Refresh Token غير صالح أو منتهي - تحتاج تحصل على Refresh Token جديد"
                elif "unsupported_grant_type" in error_msg.lower():
                    user_friendly_error = "❌ خطأ في نوع Grant - تأكد إن البيانات صحيحة"
                else:
                    user_friendly_error = f"❌ رفض Amazon الاتصال: {error_msg[:150]}"
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                user_friendly_error = "❌ فشل الاتصال بـ Amazon - تأكد من الإنترنت"
            else:
                user_friendly_error = f"❌ فشل الاتصال بـ Amazon: {error_msg[:150]}"
            
            return {
                "is_valid": False,
                "error": user_friendly_error,
                "checked_at": datetime.now().isoformat(),
            }
    
    except Exception as e:
        logger.error(f"خطأ في التحقق من SP-API: {e}", exc_info=True)
        return {
            "is_valid": False,
            "error": f"خطأ غير متوقع: {str(e)[:200]}",
        }
