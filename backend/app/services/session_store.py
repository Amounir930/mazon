"""
Session Store
Handles encryption, storage, and retrieval of browser cookies & auth sessions.

Security:
- Cookies are encrypted using Fernet symmetric encryption
- Encryption key is stored in APPDATA (not hardcoded)
- Sessions can be invalidated individually or globally
"""
import os
import json
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session as DbSession

from app.database import SessionLocal
from app.models.session import Session


# ============================================================
# Encryption Setup
# ============================================================

APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

KEY_FILE = APP_DATA_DIR / "session.key"


def _get_or_create_key() -> bytes:
    """Get existing encryption key or create a new one"""
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
        logger.debug("Loaded existing encryption key")
    else:
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        KEY_FILE.chmod(0o600)  # Owner-only access on Unix
        logger.info("Generated new encryption key")
    return key


def get_fernet() -> Fernet:
    """Get Fernet cipher instance"""
    key = _get_or_create_key()
    return Fernet(key)


# ============================================================
# Encryption Helpers
# ============================================================

def encrypt_data(data: str) -> str:
    """Encrypt a string and return base64-encoded ciphertext"""
    fernet = get_fernet()
    encrypted = fernet.encrypt(data.encode("utf-8"))
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt a base64-encoded ciphertext string"""
    fernet = get_fernet()
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
    try:
        return fernet.decrypt(encrypted_bytes).decode("utf-8")
    except InvalidToken:
        raise ValueError("Failed to decrypt session data - key may have changed")


# ============================================================
# Temporary OTP Sessions (in-memory, short-lived)
# ============================================================

_temp_sessions: Dict[str, Any] = {}


def save_temp_session(email: str, browser_auth_instance: Any) -> str:
    """Save a temporary session for OTP completion"""
    import uuid
    session_id = str(uuid.uuid4())
    _temp_sessions[session_id] = {
        "email": email,
        "auth_instance": browser_auth_instance,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"Temporary OTP session created: {session_id}")
    return session_id


def get_temp_session(session_id: str) -> Optional[dict]:
    """Get a temporary session by ID"""
    return _temp_sessions.get(session_id)


def remove_temp_session(session_id: str):
    """Remove a temporary session"""
    _temp_sessions.pop(session_id, None)


# ============================================================
# Session CRUD
# ============================================================

def save_browser_session(
    email: str,
    country_code: str,
    cookies: List[Dict[str, Any]],
    seller_name: str,
    expires_at: Optional[datetime] = None,
) -> Session:
    """Save browser login session to database (encrypted cookies)"""
    db = SessionLocal()
    try:
        # Deactivate any existing active browser sessions for this email
        existing = db.query(Session).filter(
            Session.auth_method == "browser",
            Session.email == email,
            Session.is_active == True,  # noqa: E712
        ).first()
        if existing:
            existing.is_active = False
            existing.is_valid = False
            db.flush()

        # Encrypt cookies
        cookies_json = json.dumps(cookies)
        encrypted_cookies = encrypt_data(cookies_json)

        session = Session(
            auth_method="browser",
            email=email,
            country_code=country_code,
            cookies_json=encrypted_cookies,
            seller_name=seller_name,
            is_active=True,
            is_valid=True,
            last_verified_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Browser session saved: {email} ({seller_name})")
        return session
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save browser session: {e}")
        raise
    finally:
        db.close()


def save_spapi_session(
    lwa_client_id: str,
    lwa_client_secret: str,
    refresh_token: str,
    marketplace_id: str,
    aws_access_key: str = "",
    aws_secret_key: str = "",
) -> Session:
    """Save SP-API session to database"""
    db = SessionLocal()
    try:
        # Deactivate existing SP-API session
        existing = db.query(Session).filter(
            Session.auth_method == "sp_api",
            Session.is_active == True,  # noqa: E712
        ).first()
        if existing:
            existing.is_active = False
            existing.is_valid = False
            db.flush()

        session = Session(
            auth_method="sp_api",
            lwa_client_id=lwa_client_id,
            lwa_client_secret=lwa_client_secret,
            refresh_token=refresh_token,
            marketplace_id=marketplace_id,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            is_active=True,
            is_valid=True,
            last_verified_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"SP-API session saved: {lwa_client_id}")
        return session
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save SP-API session: {e}")
        raise
    finally:
        db.close()


def get_active_session() -> Optional[Session]:
    """Get the currently active session (browser or sp_api)"""
    db = SessionLocal()
    try:
        session = db.query(Session).filter(
            Session.is_active == True,  # noqa: E712
            Session.is_valid == True,  # noqa: E712
        ).first()
        return session
    finally:
        db.close()


def get_browser_cookies(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get decrypted cookies from a browser session"""
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session or not session.cookies_json:
            return None

        decrypted = decrypt_data(session.cookies_json)
        return json.loads(decrypted)
    except ValueError as e:
        logger.error(f"Cookie decryption failed: {e}")
        return None
    finally:
        db.close()


def deactivate_session(session_id: str) -> bool:
    """Deactivate a session"""
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return False

        session.is_active = False
        session.is_valid = False
        db.commit()

        logger.info(f"Session deactivated: {session_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate session: {e}")
        return False
    finally:
        db.close()


def deactivate_all_sessions():
    """Deactivate all sessions (logout all)"""
    db = SessionLocal()
    try:
        db.query(Session).filter(
            Session.is_active == True  # noqa: E712
        ).update({"is_active": False, "is_valid": False})
        db.commit()
        logger.info("All sessions deactivated")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to deactivate all sessions: {e}")
    finally:
        db.close()


def update_session_validity(session_id: str, is_valid: bool) -> bool:
    """Update session validity after verification"""
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return False

        session.is_valid = is_valid
        session.last_verified_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update session validity: {e}")
        return False
    finally:
        db.close()
