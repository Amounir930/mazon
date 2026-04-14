"""
Seller API Endpoints — Multi-Seller Support
Manage Amazon SP-API credentials and list all sellers
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.seller import Seller
from app.models.session import Session as AuthSession
from app.schemas.product import MessageResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger

router = APIRouter()


class SellerListItem(BaseModel):
    id: str
    amazon_seller_id: Optional[str] = None
    display_name: Optional[str] = None
    marketplace_id: Optional[str] = None
    is_connected: bool = False


class SellerListResponse(BaseModel):
    sellers: List[SellerListItem]
    total: int


class SellerInfoResponse(BaseModel):
    id: Optional[str] = None
    amazon_seller_id: Optional[str] = None
    display_name: Optional[str] = None
    marketplace_id: Optional[str] = None
    region: Optional[str] = None
    is_connected: bool = False
    last_sync_at: Optional[str] = None
    has_browser_session: bool = False
    cookie_count: int = 0
    message: str = ""


@router.get("/info", response_model=SellerInfoResponse)
async def get_seller_info(db: Session = Depends(get_db)):
    """Get the single seller configuration + browser session status"""
    seller = db.query(Seller).first()
    if not seller:
        return SellerInfoResponse(message="No seller configured")

    # Check if there's an active browser session (cookies from PyWebView login)
    browser_session = db.query(AuthSession).filter(
        AuthSession.auth_method == "browser",
        AuthSession.is_active == True,
        AuthSession.is_valid == True,
    ).first()

    has_cookies = browser_session is not None
    cookie_count = 0
    if has_cookies and browser_session.cookies_json:
        try:
            import json
            from app.services.session_store import decrypt_data
            cookies = json.loads(decrypt_data(browser_session.cookies_json))
            cookie_count = len(cookies)
        except Exception:
            pass

    # If we have browser cookies, consider it "connected" even if SP-API isn't
    effective_connected = seller.is_connected or has_cookies

    return SellerInfoResponse(
        id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        region=seller.region,
        is_connected=effective_connected,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        has_browser_session=has_cookies,
        cookie_count=cookie_count,
        message=f"Connected via Browser (Cookies: {cookie_count})" if has_cookies else ("Connected" if seller.is_connected else "Not connected"),
    )


@router.put("/info", response_model=SellerInfoResponse)
async def update_seller_info(
    display_name: Optional[str] = None,
    marketplace_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update seller display name or marketplace"""
    seller = db.query(Seller).first()

    if not seller:
        raise HTTPException(status_code=404, detail="No seller configured. Connect Amazon first.")

    if display_name:
        seller.display_name = display_name
    if marketplace_id:
        seller.marketplace_id = marketplace_id

    db.commit()
    db.refresh(seller)

    logger.info(f"Seller info updated: {seller.display_name}")

    # Re-check browser session
    browser_session = db.query(AuthSession).filter(
        AuthSession.auth_method == "browser",
        AuthSession.is_active == True,
        AuthSession.is_valid == True,
    ).first()

    has_cookies = browser_session is not None
    cookie_count = 0
    if has_cookies and browser_session.cookies_json:
        try:
            import json
            from app.services.session_store import decrypt_data
            cookies = json.loads(decrypt_data(browser_session.cookies_json))
            cookie_count = len(cookies)
        except Exception:
            pass

    effective_connected = seller.is_connected or has_cookies

    return SellerInfoResponse(
        id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        region=seller.region,
        is_connected=effective_connected,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        has_browser_session=has_cookies,
        cookie_count=cookie_count,
        message="Updated successfully",
    )


@router.get("/list", response_model=SellerListResponse)
async def list_sellers(db: Session = Depends(get_db)):
    """عرض كل Sellers المسجلين في النظام"""
    sellers = db.query(Seller).order_by(Seller.created_at.desc()).all()

    result = []
    for s in sellers:
        # Check browser session
        browser_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
            AuthSession.is_valid == True,
        ).first()

        result.append(SellerListItem(
            id=str(s.id),
            amazon_seller_id=s.amazon_seller_id,
            display_name=s.display_name,
            marketplace_id=s.marketplace_id,
            is_connected=s.is_connected or (browser_session is not None),
        ))

    return SellerListResponse(sellers=result, total=len(result))


@router.delete("/disconnect", response_model=MessageResponse)
async def disconnect_seller(db: Session = Depends(get_db)):
    """Disconnect the seller (reset connection status)"""
    seller = db.query(Seller).first()

    if not seller:
        raise HTTPException(status_code=404, detail="No seller configured")

    seller.is_connected = False
    db.commit()

    logger.info("Seller disconnected")
    return {"message": "Disconnected successfully"}
