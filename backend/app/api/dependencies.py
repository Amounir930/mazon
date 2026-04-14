"""
FastAPI Dependencies
====================
Centralized dependency injection for:
- SP-API Client (with ENV fallback when no browser session)
- Database sessions (already in database.py, re-exported here for convenience)

This eliminates the anti-pattern of repeating auth logic in every endpoint.

Auth flow (priority order):
1. Browser session (AuthSession with decrypted credentials)
2. ENV fallback (SP_API_SELLER_ID, SP_API_MARKETPLACE_ID, SP_API_COUNTRY)
"""
import json
import os
from typing import Generator

from fastapi import Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data
from app.services.sp_api_client import SPAPIClient


def get_sp_api_client(
    db: Session = Depends(get_db),
) -> SPAPIClient:
    """
    Dependency that provides an authenticated SP-API client.

    Auth flow (priority order):
    1. Browser session (AuthSession with decrypted credentials)
    2. ENV fallback (SP_API_MARKETPLACE_ID, SP_API_COUNTRY from .env)

    Usage in routers:
        @router.delete("/listing/{seller_id}/{sku}")
        async def delete_listing(
            seller_id: str,
            sku: str,
            client: SPAPIClient = Depends(get_sp_api_client)
        ):
            result = client.delete_listing_item(seller_id, sku)
            return {"success": True, "status": result.get("status")}
    """
    # Try browser session first
    auth_session = (
        db.query(AuthSession)
        .filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,  # noqa: E712
        )
        .order_by(AuthSession.created_at.desc())
        .first()
    )

    if auth_session and auth_session.credentials_json:
        try:
            credentials = json.loads(decrypt_data(auth_session.credentials_json))
            marketplace_id = auth_session.marketplace_id or os.getenv("SP_API_MARKETPLACE_ID", "ARBP9OOSHTCHU")
            country_code = auth_session.country_code or os.getenv("SP_API_COUNTRY", "eg")

            logger.info(
                f"SP-API client initialized from browser session: "
                f"marketplace={marketplace_id}, country={country_code}"
            )
            return SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        except Exception as e:
            logger.warning(f"Failed to decrypt session credentials, falling back to ENV: {e}")

    # Fallback to ENV credentials (from .env file)
    marketplace_id = os.getenv("SP_API_MARKETPLACE_ID", "ARBP9OOSHTCHU")
    country_code = os.getenv("SP_API_COUNTRY", "eg")

    if not os.getenv("SP_API_CLIENT_ID") or not os.getenv("SP_API_CLIENT_SECRET"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No Amazon credentials configured. Please set SP_API_CLIENT_ID/SECRET in .env or log in via browser.",
        )

    logger.info(
        f"SP-API client initialized from .env: "
        f"marketplace={marketplace_id}, country={country_code}"
    )
    return SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)


def get_seller_id_from_session(
    db: Session = Depends(get_db),
) -> str:
    """
    Dependency that extracts the seller ID.

    Priority:
    1. Browser session credentials
    2. ENV fallback (SP_API_SELLER_ID)
    """
    auth_session = (
        db.query(AuthSession)
        .filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,  # noqa: E712
        )
        .order_by(AuthSession.created_at.desc())
        .first()
    )

    # Try session first
    if auth_session and auth_session.credentials_json:
        try:
            credentials = json.loads(decrypt_data(auth_session.credentials_json))
            seller_id = credentials.get("seller_id")
            if seller_id:
                return seller_id
        except Exception:
            pass  # Fall through to ENV

    # Fallback to ENV
    seller_id = os.getenv("SP_API_SELLER_ID")
    if seller_id:
        return seller_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Seller ID not found. Please set SP_API_SELLER_ID in .env or log in via browser.",
    )
