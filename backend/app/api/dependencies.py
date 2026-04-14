"""
FastAPI Dependencies
====================
Centralized dependency injection for:
- SP-API Client (with session/auth handling)
- Database sessions (already in database.py, re-exported here for convenience)

This eliminates the anti-pattern of repeating auth logic in every endpoint.
"""
import json
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

    Handles:
    1. Fetching the latest active browser session
    2. Decrypting credentials
    3. Initializing the SP-API client

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
    # Fetch the most recent active browser session
    auth_session = (
        db.query(AuthSession)
        .filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,  # noqa: E712
        )
        .order_by(AuthSession.created_at.desc())
        .first()
    )

    if not auth_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active Amazon session found. Please log in first.",
        )

    # Decrypt and parse credentials
    if not auth_session.credentials_json:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session credentials are missing. Please re-authenticate.",
        )

    try:
        credentials = json.loads(decrypt_data(auth_session.credentials_json))
    except Exception as e:
        logger.error(f"Failed to decrypt session credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt session credentials.",
        )

    # Extract marketplace and country from session
    marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
    country_code = auth_session.country_code or "eg"

    logger.debug(
        f"SP-API client initialized from session: "
        f"marketplace={marketplace_id}, country={country_code}"
    )

    return SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)


def get_seller_id_from_session(
    db: Session = Depends(get_db),
) -> str:
    """
    Dependency that extracts the seller ID from the active session.

    Use this when you need the seller ID independently from the SP-API client.
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

    if not auth_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active Amazon session found.",
        )

    if not auth_session.credentials_json:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session credentials are missing.",
        )

    try:
        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        seller_id = credentials.get("seller_id")
        if not seller_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seller ID not found in session credentials.",
            )
        return seller_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract seller_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract seller ID from session.",
        )
